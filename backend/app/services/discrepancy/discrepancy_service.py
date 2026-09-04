import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.models.product import Product
from app.models.detected_field import DetectedField


class DiscrepancyService:
    """
    Conservative Discrepancy Detection Service.
    Compares registered catalog product baseline against package declarations extracted from OCR.
    Guardrail: If catalog data is unavailable or evidence is insufficient, returns NEEDS_REVIEW
    rather than assuming non-compliance. Never makes automatic legal/enforcement determinations.
    """

    @classmethod
    def check_discrepancies(cls, scan_id: str, db: Session) -> Dict[str, Any]:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return {"total_discrepancies": 0, "discrepancies": [], "summary": "Scan session not found"}

        product: Optional[Product] = scan.product
        detected_fields_db = db.query(DetectedField).filter(DetectedField.scan_id == scan_id).all()
        fields_map: Dict[str, DetectedField] = {df.field_name: df for df in detected_fields_db}

        discrepancies: List[Dict[str, Any]] = []

        # Case 1: Barcode not scanned or not registered in catalog
        if not scan.barcode:
            discrepancies.append({
                "field": "barcode",
                "status": "NEEDS_REVIEW",
                "catalog_value": None,
                "detected_value": None,
                "difference_summary": "Barcode was not scanned. Catalog baseline comparison skipped; physical inspection required.",
                "severity": "LOW"
            })
            return {
                "barcode": None,
                "product_id": None,
                "product_name": None,
                "has_catalog_baseline": False,
                "total_discrepancies": 0,
                "items_needing_review": 1,
                "discrepancies": discrepancies,
                "summary": "No barcode provided; catalog baseline unavailable. Physical inspection required."
            }

        if not product:
            discrepancies.append({
                "field": "product_catalog_registration",
                "status": "NEEDS_REVIEW",
                "catalog_value": None,
                "detected_value": scan.barcode,
                "difference_summary": f"Scanned barcode '{scan.barcode}' is not registered in the product catalog database. Officer verification advised.",
                "severity": "MEDIUM"
            })
            return {
                "barcode": scan.barcode,
                "product_id": None,
                "product_name": None,
                "has_catalog_baseline": False,
                "total_discrepancies": 0,
                "items_needing_review": 1,
                "discrepancies": discrepancies,
                "summary": f"Barcode '{scan.barcode}' not found in registered catalog; conservative evaluation requires manual review."
            }

        # Case 2: Catalog baseline exists - compare fields conservatively

        # A. Net Quantity Comparison
        pkg_net_qty = fields_map.get("net_quantity")
        if not pkg_net_qty or not pkg_net_qty.value:
            discrepancies.append({
                "field": "net_quantity",
                "status": "NEEDS_REVIEW",
                "catalog_value": product.expected_net_quantity,
                "detected_value": None,
                "difference_summary": f"Expected '{product.expected_net_quantity}' from catalog, but net quantity could not be confirmed on packaging.",
                "severity": "HIGH"
            })
        else:
            norm_pkg_qty = cls._normalize_quantity_string(pkg_net_qty.value)
            norm_cat_qty = cls._normalize_quantity_string(product.expected_net_quantity or "")
            if norm_pkg_qty and norm_cat_qty and norm_pkg_qty != norm_cat_qty:
                discrepancies.append({
                    "field": "net_quantity",
                    "status": "POTENTIAL_DISCREPANCY",
                    "catalog_value": product.expected_net_quantity,
                    "detected_value": pkg_net_qty.value,
                    "difference_summary": f"Package declares '{pkg_net_qty.value}', but registered catalog value is '{product.expected_net_quantity}'.",
                    "severity": "HIGH"
                })
            elif not norm_pkg_qty:
                discrepancies.append({
                    "field": "net_quantity",
                    "status": "NEEDS_REVIEW",
                    "catalog_value": product.expected_net_quantity,
                    "detected_value": pkg_net_qty.value,
                    "difference_summary": f"Package quantity text '{pkg_net_qty.value}' requires officer manual verification against catalog '{product.expected_net_quantity}'.",
                    "severity": "MEDIUM"
                })

        # B. MRP Comparison (Overcharging detection)
        pkg_mrp = fields_map.get("mrp")
        cat_price = cls._extract_numeric_price(product.expected_mrp)
        catalog_display_mrp = f"₹ {cat_price:.2f}" if cat_price is not None else (product.expected_mrp or None)
        if not pkg_mrp or not pkg_mrp.value:
            discrepancies.append({
                "field": "mrp",
                "status": "NEEDS_REVIEW",
                "catalog_value": catalog_display_mrp,
                "detected_value": None,
                "difference_summary": f"Expected MRP {catalog_display_mrp} from catalog, but MRP could not be detected on packaging.",
                "severity": "HIGH"
            })
        else:
            pkg_price = cls._extract_numeric_price(pkg_mrp.value)

            if pkg_price is not None and cat_price is not None:
                # Discrepancy if difference exceeds tolerance of Rs. 0.50
                diff = round(pkg_price - cat_price, 2)
                if diff > 0.50:
                    discrepancies.append({
                        "field": "mrp",
                        "status": "POTENTIAL_DISCREPANCY",
                        "catalog_value": catalog_display_mrp,
                        "detected_value": f"₹ {pkg_price:.2f}",
                        "difference_summary": f"Potential Overcharging: Package declares ₹{pkg_price:.2f} exceeding registered catalog MRP of {catalog_display_mrp} by ₹{diff:.2f}.",
                        "severity": "CRITICAL"
                    })
                elif diff < -0.50:
                    discrepancies.append({
                        "field": "mrp",
                        "status": "INFO",
                        "catalog_value": catalog_display_mrp,
                        "detected_value": f"₹ {pkg_price:.2f}",
                        "difference_summary": f"Package printed MRP ₹{pkg_price:.2f} is lower than catalog standard {catalog_display_mrp} (promotional / discounted pack).",
                        "severity": "LOW"
                    })
            else:
                discrepancies.append({
                    "field": "mrp",
                    "status": "NEEDS_REVIEW",
                    "catalog_value": catalog_display_mrp,
                    "detected_value": pkg_mrp.value,
                    "difference_summary": f"Package price text '{pkg_mrp.value}' could not be parsed numerically; manual review required.",
                    "severity": "MEDIUM"
                })

        # C. Product Name / Brand Comparison
        pkg_name = fields_map.get("product_name")
        if pkg_name and pkg_name.value and product.name:
            cat_words = set(re.findall(r"\w+", product.name.lower()))
            pkg_words = set(re.findall(r"\w+", pkg_name.value.lower()))
            # If no common words between detected name and catalog name
            common = cat_words.intersection(pkg_words)
            if not common and len(cat_words) > 0 and len(pkg_words) > 0:
                discrepancies.append({
                    "field": "product_name",
                    "status": "NEEDS_REVIEW",
                    "catalog_value": product.name,
                    "detected_value": pkg_name.value,
                    "difference_summary": f"Package name '{pkg_name.value}' differs from catalog name '{product.name}'. Verify variant/packaging update.",
                    "severity": "MEDIUM"
                })

        p_disc_count = sum(1 for d in discrepancies if d["status"] == "POTENTIAL_DISCREPANCY")
        review_count = sum(1 for d in discrepancies if d["status"] == "NEEDS_REVIEW")

        if p_disc_count > 0:
            summary = f"Detected {p_disc_count} potential discrepancy(ies) between catalog registration and package declarations."
        elif review_count > 0:
            summary = f"Catalog comparison found {review_count} item(s) requiring officer verification."
        else:
            summary = "All detected package declarations match registered catalog specifications."

        return {
            "barcode": scan.barcode,
            "product_id": product.id,
            "product_name": product.name,
            "has_catalog_baseline": True,
            "total_discrepancies": p_disc_count,
            "items_needing_review": review_count,
            "discrepancies": discrepancies,
            "summary": summary
        }

    @staticmethod
    def _normalize_quantity_string(qty_str: str) -> Optional[str]:
        if not qty_str:
            return None
        clean = qty_str.strip().lower()
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([a-z\u0900-\u097F]+)", clean)
        if match:
            num = match.group(1)
            unit = match.group(2)
            # Normalize unit aliases
            unit_map = {
                "gm": "g", "gms": "g", "grams": "g", "ग्राम": "g",
                "kilograms": "kg", "किग्रा": "kg",
                "millilitres": "ml", "मिली": "ml",
                "litres": "l", "ltr": "l", "लीटर": "l",
                "pieces": "pcs", "count": "pcs", "units": "pcs", "नग": "pcs", "n": "pcs"
            }
            norm_unit = unit_map.get(unit, unit)
            return f"{float(num):.2f} {norm_unit}"
        return None

    @staticmethod
    def _extract_numeric_price(mrp_str: str) -> Optional[float]:
        if not mrp_str:
            return None
        match = re.search(r"(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]{1,2})?)", mrp_str, re.IGNORECASE)
        if match and match.group(1):
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None
