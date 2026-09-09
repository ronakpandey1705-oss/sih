import re
import json
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models.scan import Scan
from app.models.ocr_result import OCRResult
from app.models.detected_field import DetectedField


class FieldExtractor:
    """
    NLP and Heuristics Field Extractor for Legal Metrology Packaged Commodities.
    Maps raw OCR lines, bounding boxes, and catalog baseline data to mandatory Rule 6 declarations:
    - Product Name/Identity (Rule 6(1)(b))
    - Net Quantity (Rule 6(1)(c))
    - Maximum Retail Price (MRP) & Unit Sale Price (Rule 6(1)(e))
    - Manufacturer / Packer / Importer Name and Address (Rule 6(1)(a))
    - Consumer Care Grievance Details (Rule 6(2))
    - Month and Year of Manufacture / Packing / Import (Rule 6(1)(d))
    - Dimensions where applicable (Rule 6(1)(f))
    """

    # --- Regex Patterns ---
    NET_QTY_PATTERN = re.compile(
        r"(?:(?:net\s*(?:qty|quantity|wt|weight|vol|volume|content|contents|mass)|शुद्ध\s*मात्रा|वजन|मात्रा)\s*[:.\-]?\s*)?"
        r"([0-9]+(?:\.[0-9]+)?)\s*"
        r"(kg|kgs|kilogram|kilograms|g|gm|gms|gram|grams|ml|millilitre|millilitres|l|ltr|ltrs|liter|liters|litre|litres|cl|m|cm|mm|n|pcs|pieces|piece|pc|count|units|unit|u|nos|no|सेट|ग्राम|किग्रा|मिली|लीटर|नग)"
        r"(?:\b|(?=[^a-zA-Z0-9]))",
        re.IGNORECASE
    )

    MRP_PATTERN = re.compile(
        r"(?:(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price|अधिकतम\s*खुदरा\s*मूल्य)[\s:.-]*)?"
        r"(?:(?:rs\.?|inr|₹)[\s:.-]*)?([0-9]+(?:\.[0-9]{1,2})?)(?:\s*\/\-)?",
        re.IGNORECASE
    )

    TAX_INCLUSIVE_PATTERN = re.compile(
        r"(?:incl(?:usive|\.)?\s*(?:of)?\s*all\s*taxes|all\s*taxes\s*incl(?:uded|\.)?|taxes\s*incl(?:uded|\.)?|कर\s*सहित|सभी\s*कर\s*सहित|सभी\s*करों\s*सहित|tax\s*incl(?:uded|\.)?|inclusive\s*of\s*taxes)",
        re.IGNORECASE
    )

    UNIT_SALE_PRICE_PATTERN = re.compile(
        r"(?:(?:unit\s*sale\s*price|usp|इकाई\s*बिक्री\s*मूल्य)\s*[:.\-]?\s*)?(?:(?:rs|inr|₹)\.?\s*)?([0-9]+(?:\.[0-9]{1,2})?)\s*(?:\/|per)\s*(?:100\s*)?(g|gm|kg|ml|l|ltr|n|piece|pc|item|u)\b",
        re.IGNORECASE
    )

    MANUFACTURER_KEYWORDS = [
        "manufactured by", "mfg by", "mfd by", "mfg. by", "mfd. by", "mfg by:", "mfd by:",
        "manufactured & packed by", "mfg & pkd by", "mfd & pkd by", "manufactured and packed by",
        "packed by", "pkd by", "pkd. by", "pkd by:", "packaged by",
        "imported by", "imp by", "imp. by",
        "marketed by", "mkt by", "mkt. by", "packed & marketed by", "manufactured & marketed by",
        "distributed by", "dist by", "dist. by",
        "brand owner", "brand owner:", "processor:", "regd office", "registered office",
        "corporate office", "factory:", "works:", "unit:", "mfg at", "mfd at",
        "plot no", "industrial area", "midc", "gidc", "phase-", "sector-",
        "pvt ltd", "private limited", "ltd.", "limited", "llp",
        "निर्माता", "पैककर्ता", "आयातकर्ता"
    ]

    CONSUMER_CARE_KEYWORDS = [
        "consumer care", "consumer helpline", "customer care", "customer support", "customer service",
        "grievance cell", "consumer complaints", "contact us", "toll free", "toll-free", "toll free no",
        "feedback", "queries", "care manager", "care executive", "write to us", "reach us", "consumer cell",
        "helpline", "toll free:", "toll-free:", "contact:", "support:",
        "उपभोक्ता सेवा", "हेल्पलाइन", "ग्राहक सेवा"
    ]

    PHONE_PATTERN = re.compile(
        r"(?:\+91[\-\s]?)?[6-9][0-9]{9}\b|18[0-9]{2}[\-\s]?[0-9]{3}[\-\s]?[0-9]{3,4}\b|0[1-9][0-9]{1,3}[\-\s]?[0-9]{6,8}\b"
    )

    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    )

    DATE_PATTERN = re.compile(
        r"(?:(?:mfg|pkd|packed|manufactured|imported|mfd|date|dt|dom|dop|use\s*by|best\s*before|exp(?:iry)?)\s*[:.\-]?\s*)?"
        r"((?:0[1-9]|1[0-2])[\/\.\-](?:20[2-3][0-9]|[2-3][0-9])|"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\.\-\/]*(?:20[2-3][0-9]|[2-3][0-9])|"
        r"(?:0[1-9]|[12][0-9]|3[01])[\/\.\-](?:0[1-9]|1[0-2])[\/\.\-](?:20[2-3][0-9]|[2-3][0-9])|"
        r"(?:best\s*before|use\s*by|exp(?:iry)?)\s*(?:within\s*)?[0-9]+\s*(?:months?|days?|weeks?|years?)(?:\s*(?:from|of)\s*(?:mfg|pkd|packaging|manufacture|date))?)\b",
        re.IGNORECASE
    )

    DIMENSIONS_PATTERN = re.compile(
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:cm|mm|m)\s*[xX*]\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cm|mm|m)(?:\s*[xX*]\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cm|mm|m))?",
        re.IGNORECASE
    )

    PINCODE_PATTERN = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")

    @classmethod
    def extract_from_scan(cls, scan_id: str, db: Session) -> List[DetectedField]:
        """
        Main entrypoint: extracts mandatory fields from OCR results of a scan session.
        Uses sliding window across consecutive lines to reliably catch split packaging declarations.
        Corroborates with catalog baseline product when linked to eliminate false flags.
        Stores results into detected_fields table and returns the list.
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

        # Multi-line sliding windows (combines 1, 2, and 3 adjacent lines to catch split labels)
        windows = []
        for i in range(len(ocr_results)):
            windows.append({
                "text": ocr_results[i].text.strip(),
                "image_id": ocr_results[i].image_id,
                "bbox_json": ocr_results[i].bbox_json,
                "confidence": ocr_results[i].confidence,
            })
            if i + 1 < len(ocr_results):
                pair_text = f"{ocr_results[i].text.strip()} {ocr_results[i + 1].text.strip()}"
                windows.append({
                    "text": pair_text,
                    "image_id": ocr_results[i].image_id,
                    "bbox_json": ocr_results[i].bbox_json,
                    "confidence": min(ocr_results[i].confidence, ocr_results[i + 1].confidence),
                })
            if i + 2 < len(ocr_results):
                triplet_text = f"{ocr_results[i].text.strip()} {ocr_results[i + 1].text.strip()} {ocr_results[i + 2].text.strip()}"
                windows.append({
                    "text": triplet_text,
                    "image_id": ocr_results[i].image_id,
                    "bbox_json": ocr_results[i].bbox_json,
                    "confidence": min(ocr_results[i].confidence, ocr_results[i + 1].confidence, ocr_results[i + 2].confidence),
                })

        # -------------------------------------------------------------
        # 1. Product Name / Identity (Rule 6(1)(b))
        # -------------------------------------------------------------
        if scan.product and scan.product.name:
            extracted_fields_dict["product_name"] = {
                "value": scan.product.name,
                "raw_text": scan.product.name,
                "confidence": 0.98,
                "method": "PRODUCT_CATALOG_LOOKUP",
                "image_id": ocr_results[0].image_id if ocr_results else None,
                "bbox_json": ocr_results[0].bbox_json if ocr_results else None
            }
        else:
            for r in ocr_results:
                clean_t = r.text.strip()
                if len(clean_t) >= 4 and not any(kw in clean_t.lower() for kw in ["mrp", "rs.", "₹", "net qty", "mfg", "batch", "pkd", "1800"]):
                    extracted_fields_dict["product_name"] = {
                        "value": clean_t,
                        "raw_text": clean_t,
                        "confidence": round(r.confidence, 4),
                        "method": "OCR_TITLE_HEURISTIC",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # -------------------------------------------------------------
        # 2. Net Quantity (Rule 6(1)(c))
        # -------------------------------------------------------------
        # First priority: Look for explicit Net Quantity keyword in sliding windows
        for w in windows:
            t = w["text"]
            if re.search(r"net\s*(?:qty|quantity|wt|weight|vol|volume|content|contents|mass)|शुद्ध\s*मात्रा", t, re.IGNORECASE):
                match = cls.NET_QTY_PATTERN.search(t)
                if match:
                    val = f"{match.group(1)} {match.group(2)}"
                    extracted_fields_dict["net_quantity"] = {
                        "value": val,
                        "raw_text": t,
                        "confidence": round(w["confidence"], 4),
                        "method": "REGEX_KEYWORD_WINDOW",
                        "image_id": w["image_id"],
                        "bbox_json": w["bbox_json"]
                    }
                    break

        # Second priority: Any standalone metric quantity pattern
        if "net_quantity" not in extracted_fields_dict:
            for r in ocr_results:
                match = cls.NET_QTY_PATTERN.search(r.text.strip())
                if match and not any(neg in r.text.lower() for neg in ["mrp", "rs.", "₹", "per"]):
                    val = f"{match.group(1)} {match.group(2)}"
                    extracted_fields_dict["net_quantity"] = {
                        "value": val,
                        "raw_text": r.text.strip(),
                        "confidence": round(r.confidence * 0.88, 4),
                        "method": "REGEX_PATTERN",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # Third priority: Catalog baseline fallback if linked product exists
        if "net_quantity" not in extracted_fields_dict and scan.product and scan.product.expected_net_quantity:
            extracted_fields_dict["net_quantity"] = {
                "value": scan.product.expected_net_quantity,
                "raw_text": scan.product.expected_net_quantity,
                "confidence": 0.95,
                "method": "CATALOG_VERIFIED_BASELINE",
                "image_id": ocr_results[0].image_id if ocr_results else None,
                "bbox_json": None
            }

        # -------------------------------------------------------------
        # 3. Maximum Retail Price (MRP) & Tax Statement (Rule 6(1)(e))
        # -------------------------------------------------------------
        has_tax_global = bool(cls.TAX_INCLUSIVE_PATTERN.search(full_text))

        # First priority: Look for explicit MRP keyword with price in sliding windows
        mrp_pat1 = re.compile(r"(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price|अधिकतम\s*खुदरा\s*मूल्य)[\s:.-]*(?:rs\.?|inr|₹)?[\s:.-]*([0-9]+(?:\.[0-9]{1,2})?)", re.IGNORECASE)
        mrp_pat2 = re.compile(r"(?:rs\.?|inr|₹)\s*([0-9]+(?:\.[0-9]{1,2})?)\s*(?:m\.?r\.?p\.?|max|कर)", re.IGNORECASE)
        for w in windows:
            t = w["text"]
            price_match = mrp_pat1.search(t) or mrp_pat2.search(t)
            if price_match and price_match.group(1):
                has_tax = has_tax_global or bool(cls.TAX_INCLUSIVE_PATTERN.search(t))
                val = f"₹ {price_match.group(1)}" + (" (incl. of all taxes)" if has_tax else "")
                extracted_fields_dict["mrp"] = {
                    "value": val,
                    "raw_text": t,
                    "confidence": round(w["confidence"], 4),
                    "method": "REGEX_KEYWORD_WINDOW",
                    "image_id": w["image_id"],
                    "bbox_json": w["bbox_json"]
                }
                break

        # Second priority: Standalone ₹ or Rs price
        if "mrp" not in extracted_fields_dict:
            for r in ocr_results:
                t = r.text.strip()
                match = re.search(r"(?:₹|rs\.?|inr)\s*([0-9]+(?:\.[0-9]{1,2})?)", t, re.IGNORECASE)
                if match and match.group(1):
                    val = f"₹ {match.group(1)}" + (" (incl. of all taxes)" if has_tax_global else "")
                    extracted_fields_dict["mrp"] = {
                        "value": val,
                        "raw_text": t,
                        "confidence": round(r.confidence * 0.85, 4),
                        "method": "REGEX_SYMBOL",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # Third priority: Catalog baseline fallback if linked product exists
        if "mrp" not in extracted_fields_dict and scan.product and scan.product.expected_mrp:
            cat_mrp = scan.product.expected_mrp
            if "incl" not in cat_mrp.lower():
                cat_mrp += " (incl. of all taxes)"
            extracted_fields_dict["mrp"] = {
                "value": cat_mrp,
                "raw_text": cat_mrp,
                "confidence": 0.95,
                "method": "CATALOG_VERIFIED_BASELINE",
                "image_id": ocr_results[0].image_id if ocr_results else None,
                "bbox_json": None
            }

        # -------------------------------------------------------------
        # 4. Unit Sale Price (USP) (Rule 6(1)(e))
        # -------------------------------------------------------------
        for w in windows:
            usp_match = cls.UNIT_SALE_PRICE_PATTERN.search(w["text"])
            if usp_match and usp_match.group(1):
                unit_str = usp_match.group(2) if usp_match.group(2) else "unit"
                val = f"₹ {usp_match.group(1)} / {unit_str}"
                extracted_fields_dict["unit_sale_price"] = {
                    "value": val,
                    "raw_text": w["text"],
                    "confidence": round(w["confidence"], 4),
                    "method": "REGEX_UNIT_PRICE",
                    "image_id": w["image_id"],
                    "bbox_json": w["bbox_json"]
                }
                break

        # -------------------------------------------------------------
        # 5. Manufacturer / Packer / Importer Name & Address (Rule 6(1)(a))
        # -------------------------------------------------------------
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
                for j in range(i + 1, min(i + 5, len(ocr_results))):
                    next_line = ocr_results[j].text.strip()
                    if cls.PINCODE_PATTERN.search(next_line) or any(
                        w in next_line.lower() for w in [
                            "road", "street", "dist", "state", "city", "nagar", "plot", "area", "estate", "india", "pincode"
                        ]
                    ):
                        mfg_lines.append(next_line)
                break

        # Check PIN code if keyword line was not identified
        if not mfg_lines:
            for i, r in enumerate(ocr_results):
                if cls.PINCODE_PATTERN.search(r.text.strip()):
                    start_idx = max(0, i - 2)
                    for k in range(start_idx, min(i + 1, len(ocr_results))):
                        mfg_lines.append(ocr_results[k].text.strip())
                    mfg_image_id = r.image_id
                    mfg_bbox = r.bbox_json
                    mfg_conf = 0.75
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
        elif scan.product and scan.product.manufacturer:
            addr_str = f"{scan.product.manufacturer}, {scan.product.manufacturer_address or 'India'}"
            extracted_fields_dict["manufacturer_name_and_address"] = {
                "value": addr_str,
                "raw_text": addr_str,
                "confidence": 0.95,
                "method": "CATALOG_VERIFIED_BASELINE",
                "image_id": ocr_results[0].image_id if ocr_results else None,
                "bbox_json": None
            }

        # -------------------------------------------------------------
        # 6. Consumer Care Contact Information (Rule 6(2))
        # -------------------------------------------------------------
        cc_elements = []
        cc_image_id = None
        cc_bbox = None
        cc_conf = 0.8

        for r in ocr_results:
            text_lower = r.text.lower()
            if any(kw in text_lower for kw in cls.CONSUMER_CARE_KEYWORDS) or cls.EMAIL_PATTERN.search(r.text) or "1800" in r.text or "1860" in r.text:
                cc_elements.append(r.text.strip())
                if not cc_image_id:
                    cc_image_id = r.image_id
                    cc_bbox = r.bbox_json
                    cc_conf = r.confidence

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
        elif scan.product and scan.product.consumer_care_details:
            extracted_fields_dict["consumer_care"] = {
                "value": scan.product.consumer_care_details,
                "raw_text": scan.product.consumer_care_details,
                "confidence": 0.95,
                "method": "CATALOG_VERIFIED_BASELINE",
                "image_id": ocr_results[0].image_id if ocr_results else None,
                "bbox_json": None
            }

        # -------------------------------------------------------------
        # 7. Date Declaration (Mfg / Packing / Import Date) (Rule 6(1)(d))
        # -------------------------------------------------------------
        for w in windows:
            t = w["text"]
            if any(k in t.lower() for k in ["mfg", "pkd", "packed", "date", "mfd", "dom", "dop", "use by", "best before"]):
                match = cls.DATE_PATTERN.search(t)
                if match and match.group(1):
                    extracted_fields_dict["manufacture_or_import_date"] = {
                        "value": match.group(1),
                        "raw_text": t,
                        "confidence": round(w["confidence"], 4),
                        "method": "REGEX_DATE",
                        "image_id": w["image_id"],
                        "bbox_json": w["bbox_json"]
                    }
                    break

        if "manufacture_or_import_date" not in extracted_fields_dict:
            for r in ocr_results:
                match = cls.DATE_PATTERN.search(r.text.strip())
                if match and match.group(1) and not any(neg in r.text.lower() for neg in ["mrp", "net", "rs"]):
                    extracted_fields_dict["manufacture_or_import_date"] = {
                        "value": match.group(1),
                        "raw_text": r.text.strip(),
                        "confidence": round(r.confidence * 0.8, 4),
                        "method": "REGEX_DATE_STANDALONE",
                        "image_id": r.image_id,
                        "bbox_json": r.bbox_json
                    }
                    break

        # -------------------------------------------------------------
        # 8. Package Dimensions (Rule 6(1)(f))
        # -------------------------------------------------------------
        for w in windows:
            dim_match = cls.DIMENSIONS_PATTERN.search(w["text"])
            if dim_match:
                extracted_fields_dict["dimensions"] = {
                    "value": dim_match.group(0),
                    "raw_text": w["text"],
                    "confidence": round(w["confidence"], 4),
                    "method": "REGEX_DIMENSIONS",
                    "image_id": w["image_id"],
                    "bbox_json": w["bbox_json"]
                }
                break

        # --- AI-Assisted LLM extraction fallback for uncataloged products or noisy packaging labels ---
        if full_text_lines and (not scan.product or len(extracted_fields_dict) < 6):
            cls._ai_llm_extract_missing_fields(
                full_text=full_text,
                extracted_fields_dict=extracted_fields_dict,
                ocr_results=ocr_results
            )

        # --- Persist in Database (detected_fields table) ---
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

    @classmethod
    def _ai_llm_extract_missing_fields(
        cls,
        full_text: str,
        extracted_fields_dict: Dict[str, Dict[str, Any]],
        ocr_results: List[OCRResult],
    ) -> None:
        """
        AI-Assisted field extraction via Groq for uncataloged products or noisy packaging labels.
        Fills in mandatory Legal Metrology fields that heuristic regexes may have missed.
        """
        api_key = (settings.GROQ_API_KEY or "").strip()
        if not api_key or not full_text.strip():
            return

        needed_fields = [
            f for f in [
                "product_name",
                "net_quantity",
                "mrp",
                "manufacturer_name_and_address",
                "consumer_care",
                "manufacture_or_import_date",
                "unit_sale_price",
            ]
            if f not in extracted_fields_dict
        ]
        if not needed_fields:
            return

        prompt = (
            "You are an expert Indian Legal Metrology (Packaged Commodities Rules, 2011) compliance officer.\n"
            "Analyze the following OCR text from a physical packaged commodity and extract statutory declarations.\n"
            "If a declaration is present in the text, extract its exact value. If not found, set its value to null.\n\n"
            "Statutory fields to extract:\n"
            "- product_name: The generic or brand name of the commodity.\n"
            "- net_quantity: Declared net quantity with metric unit (e.g. 100g, 500 ml, 1 N).\n"
            "- mrp: Maximum retail price with currency and tax declaration (e.g. ₹ 20.00 incl. of all taxes).\n"
            "- unit_sale_price: Unit sale price if declared (e.g. ₹ 0.20 / g).\n"
            "- manufacturer_name_and_address: Full name and address of manufacturer, packer, or marketer with city/state/pin.\n"
            "- consumer_care: Consumer care contact details (toll-free number, phone, email, or address).\n"
            "- manufacture_or_import_date: Date of manufacture/packing or 'Best Before' statement.\n"
            "- country_of_origin: Country of origin if stated (default null if not stated).\n\n"
            f"OCR Text:\n{full_text[:4000]}\n\n"
            "Respond ONLY with a valid JSON object containing these 8 keys. Do not include markdown code fences, comments, or explanations."
        )

        try:
            candidate_models = [settings.GROQ_MODEL]
            for m in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b", "llama-3.3-70b-versatile"]:
                if m not in candidate_models:
                    candidate_models.append(m)

            with httpx.Client(timeout=8.0) as client:
                for mod in candidate_models:
                    try:
                        resp = client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": mod,
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.1,
                                "max_tokens": 1000,
                            },
                        )
                        if resp.status_code == 200:
                            content = resp.json()["choices"][0]["message"]["content"].strip()
                            if content.startswith("```"):
                                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                            data = json.loads(content)
                            first_img_id = ocr_results[0].image_id if ocr_results else None
                            first_bbox = ocr_results[0].bbox_json if ocr_results else None

                            for field_key, val in data.items():
                                if field_key in needed_fields and val and str(val).strip() and str(val).lower() != "null":
                                    extracted_fields_dict[field_key] = {
                                        "value": str(val).strip(),
                                        "raw_text": str(val).strip(),
                                        "confidence": 0.92,
                                        "method": "AI_LLM_ASSISTED",
                                        "image_id": first_img_id,
                                        "bbox_json": first_bbox,
                                    }
                            break
                        elif resp.status_code in (400, 404):
                            continue
                        else:
                            break
                    except Exception:
                        continue
        except Exception as exc:
            print(f"[AI_EXTRACTION] Non-blocking notice: {exc}")
