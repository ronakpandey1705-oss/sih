import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.models.ocr_result import OCRResult
from app.models.detected_field import DetectedField


class FieldExtractor:
    """
    NLP and Heuristics Field Extractor for Legal Metrology Packaged Commodities.
    Maps raw OCR lines and bounding boxes to mandatory Rule 6 declarations:
    - Product Name/Identity (Rule 6(1)(b))
    - Net Quantity (Rule 6(1)(c))
    - Maximum Retail Price (MRP) & Unit Sale Price (Rule 6(1)(e))
    - Manufacturer / Packer / Importer Name and Address (Rule 6(1)(a))
    - Consumer Care Grievance Details (Rule 6(2))
    - Month and Year of Manufacture / Packing / Import (Rule 6(1)(d))
    - Dimensions where applicable (Rule 6(1)(f))
    - Country of Origin (for imported commodities)
    """

    # --- Regex Patterns ---
    NET_QTY_PATTERN = re.compile(
        r"(?:(?:net\s*(?:qty|quantity|wt|weight)|शुद्ध\s*मात्रा)\s*[:.\-]?\s*)?([0-9]+(?:\.[0-9]+)?)\s*(kg|g|gm|gms|grams|ml|l|ltr|litres|cl|m|cm|mm|n|pcs|pieces|count|units|u|ग्राम|किग्रा|मिली|लीटर|नग)(?:\b|(?=[^a-zA-Z0-9]))",
        re.IGNORECASE
    )

    MRP_PATTERN = re.compile(
        r"(?:(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price|अधिकतम\s*खुदरा\s*मूल्य)\s*[:.\-]?\s*)?(?:(?:rs|inr|₹)\.?\s*)?([0-9]+(?:\.[0-9]{1,2})?)",
        re.IGNORECASE
    )

    TAX_INCLUSIVE_PATTERN = re.compile(
        r"(?:incl(?:usive)?\s*(?:of)?\s*all\s*taxes|कर\s*सहित|all\s*taxes\s*incl)",
        re.IGNORECASE
    )

    UNIT_SALE_PRICE_PATTERN = re.compile(
        r"(?:(?:unit\s*sale\s*price|usp|इकाई\s*बिक्री\s*मूल्य)\s*[:.\-]?\s*)?(?:(?:rs|inr|₹)\.?\s*)?([0-9]+(?:\.[0-9]{1,2})?)\s*(?:\/|per)\s*(?:100\s*)?(g|gm|kg|ml|l|ltr|n|piece|pc|item)\b",
        re.IGNORECASE
    )

    MANUFACTURER_KEYWORDS = [
        "manufactured by", "mfg by", "mfd by", "mfg. by", "mfd. by",
        "packed by", "pkd by", "pkd. by",
        "imported by", "imp by", "imp. by",
        "marketed by", "mkt by",
        "निर्माता", "पैककर्ता", "आयातकर्ता"
    ]

    CONSUMER_CARE_KEYWORDS = [
        "consumer care", "consumer helpline", "customer care", "customer support",
        "grievance cell", "consumer complaints", "contact us", "toll free",
        "उपभोक्ता सेवा", "हेल्पलाइन"
    ]

    PHONE_PATTERN = re.compile(
        r"(?:\+91[\-\s]?)?[6-9][0-9]{9}\b|1800[\-\s]?[0-9]{3}[\-\s]?[0-9]{3,4}\b"
    )

    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )

    DATE_PATTERN = re.compile(
        r"(?:(?:mfg|pkd|packed|manufactured|imported|mfd|date|dt)\s*[:.\-]?\s*)?((?:0[1-9]|1[0-2])[\/\-](?:20[2-3][0-9]|[2-3][0-9])|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(?:20[2-3][0-9]|[2-3][0-9])|(?:0[1-9]|[12][0-9]|3[01])[\/\-](?:0[1-9]|1[0-2])[\/\-](?:20[2-3][0-9]|[2-3][0-9]))\b",
        re.IGNORECASE
    )

    DIMENSIONS_PATTERN = re.compile(
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:cm|mm|m)\s*[xX*]\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cm|mm|m)(?:\s*[xX*]\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cm|mm|m))?",
        re.IGNORECASE
    )

    PINCODE_PATTERN = re.compile(r"\b[1-9][0-9]{5}\b")

    @classmethod
    def extract_from_scan(cls, scan_id: str, db: Session) -> List[DetectedField]:
        """
        Main entrypoint: extracts mandatory fields from OCR results of a scan session.
        Stores results into the detected_fields table and returns the list.
        """
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            return []

        ocr_results: List[OCRResult] = (
            db.query(OCRResult)
            .filter(OCRResult.scan_id == scan_id)
            .order_by(OCRResult.line_order)
            .all()
        )

        extracted_fields_dict: Dict[str, Dict[str, Any]] = {}

        full_text_lines = [r.text.strip() for r in ocr_results if r.text and r.text.strip()]
        full_text = " \n ".join(full_text_lines)

        # 1. Product Name / Identity
        # Use linked product name from barcode lookup if available, or first prominent line
        if scan.product and scan.product.name:
            extracted_fields_dict["product_name"] = {
                "value": scan.product.name,
                "raw_text": scan.product.name,
                "confidence": 0.95,
                "method": "PRODUCT_CATALOG_LOOKUP",
                "image_id": None,
                "bbox_json": None
            }
        else:
            for r in ocr_results:
                clean_t = r.text.strip()
                if len(clean_t) >= 4 and not any(kw in clean_t.lower() for kw in ["mrp", "rs.", "net qty", "mfg", "batch"]):
                    extracted_fields_dict["product_name"] = {
                        "value": clean_t,
                        "raw_text": clean_t,
                        "confidence": round(r.confidence, 4),
                        "method": "OCR_TITLE_HEURISTIC",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # 2. Net Quantity
        for r in ocr_results:
            text = r.text.strip()
            # Direct match with "net qty" or "net quantity"
            if re.search(r"net\s*(?:qty|quantity|wt|weight)|शुद्ध\s*मात्रा", text, re.IGNORECASE):
                match = cls.NET_QTY_PATTERN.search(text)
                if match:
                    val = f"{match.group(1)} {match.group(2)}"
                    extracted_fields_dict["net_quantity"] = {
                        "value": val,
                        "raw_text": text,
                        "confidence": round(r.confidence, 4),
                        "method": "REGEX_KEYWORD",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # If not found via keyword, search without keyword prefix
        if "net_quantity" not in extracted_fields_dict:
            for r in ocr_results:
                match = cls.NET_QTY_PATTERN.search(r.text.strip())
                if match and not any(neg in r.text.lower() for neg in ["mrp", "rs", "₹"]):
                    val = f"{match.group(1)} {match.group(2)}"
                    extracted_fields_dict["net_quantity"] = {
                        "value": val,
                        "raw_text": r.text.strip(),
                        "confidence": round(r.confidence * 0.85, 4),
                        "method": "REGEX_PATTERN",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # 3. MRP & Tax Statement
        for r in ocr_results:
            text = r.text.strip()
            if re.search(r"m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price|अधिकतम\s*खुदरा\s*मूल्य", text, re.IGNORECASE):
                price_match = re.search(r"(?:rs|inr|₹)?\.?\s*([0-9]+(?:\.[0-9]{1,2})?)", text, re.IGNORECASE)
                has_tax = bool(cls.TAX_INCLUSIVE_PATTERN.search(full_text))
                if price_match and price_match.group(1):
                    val = f"₹ {price_match.group(1)}" + (" (incl. of all taxes)" if has_tax else "")
                    extracted_fields_dict["mrp"] = {
                        "value": val,
                        "raw_text": text,
                        "confidence": round(r.confidence, 4),
                        "method": "REGEX_KEYWORD",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # Standalone Rs / ₹ price if keyword line not found
        if "mrp" not in extracted_fields_dict:
            for r in ocr_results:
                text = r.text.strip()
                match = re.search(r"(?:₹|rs\.?)\s*([0-9]+(?:\.[0-9]{1,2})?)", text, re.IGNORECASE)
                if match and match.group(1):
                    has_tax = bool(cls.TAX_INCLUSIVE_PATTERN.search(full_text))
                    val = f"₹ {match.group(1)}" + (" (incl. of all taxes)" if has_tax else "")
                    extracted_fields_dict["mrp"] = {
                        "value": val,
                        "raw_text": text,
                        "confidence": round(r.confidence * 0.8, 4),
                        "method": "REGEX_SYMBOL",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # 4. Unit Sale Price (USP)
        for r in ocr_results:
            text = r.text.strip()
            usp_match = cls.UNIT_SALE_PRICE_PATTERN.search(text)
            if usp_match and usp_match.group(1):
                unit_str = usp_match.group(2) if usp_match.group(2) else "unit"
                val = f"₹ {usp_match.group(1)} / {unit_str}"
                extracted_fields_dict["unit_sale_price"] = {
                    "value": val,
                    "raw_text": text,
                    "confidence": round(r.confidence, 4),
                    "method": "REGEX_UNIT_PRICE",
                    "image_id": r.image_id,
                    "bbox_json": r.bbox_json
                }
                break

        # 5. Manufacturer / Packer / Importer Name & Address
        mfg_lines = []
        mfg_image_id = None
        mfg_bbox = None
        mfg_conf = 0.8
        for i, r in enumerate(ocr_results):
            text_lower = r.text.lower()
            if any(kw in text_lower for kw in cls.MANUFACTURER_KEYWORDS):
                mfg_lines.append(r.text.strip())
                mfg_image_id = r.image_id
                mfg_bbox = r.bbox_json
                mfg_conf = r.confidence
                # Append subsequent lines that appear to be address (contains PIN or road/city)
                for j in range(i + 1, min(i + 4, len(ocr_results))):
                    next_line = ocr_results[j].text.strip()
                    if cls.PINCODE_PATTERN.search(next_line) or any(w in next_line.lower() for w in ["road", "street", "dist", "state", "city", "nagar", "plot", "area"]):
                        mfg_lines.append(next_line)
                break

        if mfg_lines:
            extracted_fields_dict["manufacturer_name_and_address"] = {
                "value": ", ".join(mfg_lines),
                "raw_text": " \n ".join(mfg_lines),
                "confidence": round(mfg_conf, 4),
                "method": "REGEX_KEYWORD_HEURISTIC",
                "image_id": mfg_image_id,
                "bbox_json": mfg_bbox
            }

        # 6. Consumer Care Contact Information
        cc_elements = []
        cc_image_id = None
        cc_bbox = None
        cc_conf = 0.8
        for r in ocr_results:
            text_lower = r.text.lower()
            if any(kw in text_lower for kw in cls.CONSUMER_CARE_KEYWORDS) or cls.EMAIL_PATTERN.search(r.text) or "1800" in r.text:
                cc_elements.append(r.text.strip())
                if not cc_image_id:
                    cc_image_id = r.image_id
                    cc_bbox = r.bbox_json
                    cc_conf = r.confidence

        # Look for phone numbers and email addresses across entire text
        emails = cls.EMAIL_PATTERN.findall(full_text)
        phones = cls.PHONE_PATTERN.findall(full_text)
        if emails and not any(e in " ".join(cc_elements) for e in emails):
            cc_elements.append(f"Email: {emails[0]}")
        if phones and not any(p in " ".join(cc_elements) for p in phones):
            cc_elements.append(f"Phone: {phones[0]}")

        if cc_elements:
            extracted_fields_dict["consumer_care"] = {
                "value": " | ".join(cc_elements),
                "raw_text": " \n ".join(cc_elements),
                "confidence": round(cc_conf, 4),
                "method": "REGEX_CONTACT_PATTERNS",
                "image_id": cc_image_id,
                "bbox_json": cc_bbox
            }

        # 7. Date Declaration (Mfg / Packing / Import Date)
        for r in ocr_results:
            text = r.text.strip()
            if any(k in text.lower() for k in ["mfg", "pkd", "packed", "date", "mfd", "use by", "best before"]):
                match = cls.DATE_PATTERN.search(text)
                if match and match.group(1):
                    extracted_fields_dict["manufacture_or_import_date"] = {
                        "value": match.group(1),
                        "raw_text": text,
                        "confidence": round(r.confidence, 4),
                        "method": "REGEX_DATE",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # Standalone date pattern if not found with prefix
        if "manufacture_or_import_date" not in extracted_fields_dict:
            for r in ocr_results:
                match = cls.DATE_PATTERN.search(r.text.strip())
                if match and match.group(1) and not any(neg in r.text.lower() for neg in ["mrp", "net"]):
                    extracted_fields_dict["manufacture_or_import_date"] = {
                        "value": match.group(1),
                        "raw_text": r.text.strip(),
                        "confidence": round(r.confidence * 0.75, 4),
                        "method": "REGEX_DATE_STANDALONE",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # 8. Dimensions (where applicable)
        for r in ocr_results:
            text = r.text.strip()
            dim_match = cls.DIMENSIONS_PATTERN.search(text)
            if dim_match:
                extracted_fields_dict["dimensions"] = {
                    "value": dim_match.group(0),
                    "raw_text": text,
                    "confidence": round(r.confidence, 4),
                    "method": "REGEX_DIMENSIONS",
                    "image_id": r.image_id,
                    "bbox_json": r.bbox_json
                }
                break

        # --- Persist in Database (detected_fields table) ---
        # Clear previous detections for this scan to avoid stale records
        db.query(DetectedField).filter(DetectedField.scan_id == scan_id).delete()

        saved_fields: List[DetectedField] = []
        for field_name, data in extracted_fields_dict.items():
            df = DetectedField(
                scan_id=scan_id,
                image_id=data["image_id"],
                field_name=field_name,
                value=data["value"],
                raw_text=data["raw_text"],
                confidence=data["confidence"],
                extraction_method=data["method"],
                bbox_json=data["bbox_json"]
            )
            db.add(df)
            saved_fields.append(df)

        db.commit()
        for df in saved_fields:
            db.refresh(df)

        return saved_fields
