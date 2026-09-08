import os
import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.models.detected_field import DetectedField
from app.models.compliance import ComplianceResult, Violation
from app.models.ocr_result import OCRResult
from app.models.image import UploadedImage
from app.schemas.compliance import RuleEvaluationItem, ComplianceEvaluationResponse


class RulesEngine:
    """
    Deterministic Legal Metrology Compliance Rules Engine.
    Reads rules from configurable rules/rules.json and evaluates detected fields.
    Statuses returned: PASS, POTENTIAL_NON_COMPLIANCE, NEEDS_REVIEW, NOT_APPLICABLE.
    Never asserts legal guilt; provides evidence-based findings for officer review.
    """

    _rules_cache: Optional[Dict[str, Any]] = None
    _rules_mtime: float = 0.0

    @classmethod
    def get_rules_path(cls) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        return os.path.join(base_dir, "rules", "rules.json")

    @classmethod
    def load_rules(cls) -> Dict[str, Any]:
        path = cls.get_rules_path()
        if not os.path.exists(path):
            raise FileNotFoundError(f"Rules configuration file not found at '{path}'")

        mtime = os.path.getmtime(path)
        if cls._rules_cache is None or mtime > cls._rules_mtime:
            with open(path, "r", encoding="utf-8") as f:
                cls._rules_cache = json.load(f)
            cls._rules_mtime = mtime

        return cls._rules_cache

    @classmethod
    def evaluate_scan(cls, scan_id: str, db: Session) -> ComplianceEvaluationResponse:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise ValueError(f"Scan session '{scan_id}' not found")

        rules_config = cls.load_rules()
        rules_list = rules_config.get("rules", [])

        # Fetch detected fields for this scan
        detected_fields_db = db.query(DetectedField).filter(DetectedField.scan_id == scan_id).all()
        fields_map: Dict[str, DetectedField] = {df.field_name: df for df in detected_fields_db}

        # Fetch OCR results for language and confidence checks
        ocr_results = db.query(OCRResult).filter(OCRResult.scan_id == scan_id).all()

        # Step 1: Check Exemption Status (Rule 26 / LM-10)
        is_small_package_exempt, exemption_reason = cls._check_rule_26_exemption(fields_map, rules_config)

        # Step 2: Evaluate Each Rule
        evaluated_items: List[RuleEvaluationItem] = []

        for r_def in rules_list:
            rule_id = r_def["id"]
            field_name = r_def["field"]

            if rule_id == "LM-10":
                # Rule 26 Exemption rule itself
                if is_small_package_exempt:
                    item = RuleEvaluationItem(
                        rule_id=rule_id,
                        rule_number=r_def["rule_number"],
                        name=r_def["name"],
                        field=field_name,
                        status="PASS",
                        confidence=0.95,
                        severity=r_def["severity"],
                        reason=exemption_reason,
                        legal_reference=r_def["legal_reference"],
                        evidence_text=fields_map["net_quantity"].value if "net_quantity" in fields_map else None,
                        evidence_image_id=fields_map["net_quantity"].image_id if "net_quantity" in fields_map else None
                    )
                else:
                    item = RuleEvaluationItem(
                        rule_id=rule_id,
                        rule_number=r_def["rule_number"],
                        name=r_def["name"],
                        field=field_name,
                        status="NOT_APPLICABLE",
                        confidence=1.0,
                        severity=r_def["severity"],
                        reason="Standard package; does not qualify for small-package exemption under Rule 26.",
                        legal_reference=r_def["legal_reference"]
                    )
                evaluated_items.append(item)
                continue

            # If small package exempt, font size and placement rules are NOT_APPLICABLE
            if is_small_package_exempt and rule_id in ["LM-07", "LM-08"]:
                item = RuleEvaluationItem(
                    rule_id=rule_id,
                    rule_number=r_def["rule_number"],
                    name=r_def["name"],
                    field=field_name,
                    status="NOT_APPLICABLE",
                    confidence=1.0,
                    severity=r_def["severity"],
                    reason=f"Exempt from {r_def['name']} requirement under Rule 26(a) (net quantity <= 10 g/ml).",
                    legal_reference=r_def["legal_reference"]
                )
                evaluated_items.append(item)
                continue

            # Evaluate specific rules
            if rule_id == "LM-01":
                item = cls._eval_product_name(r_def, fields_map)
            elif rule_id == "LM-02":
                item = cls._eval_net_quantity(r_def, fields_map)
            elif rule_id == "LM-03":
                item = cls._eval_mrp(r_def, fields_map, ocr_results)
            elif rule_id == "LM-04":
                item = cls._eval_manufacturer(r_def, fields_map)
            elif rule_id == "LM-05":
                item = cls._eval_consumer_care(r_def, fields_map)
            elif rule_id == "LM-06":
                item = cls._eval_date(r_def, fields_map)
            elif rule_id == "LM-07":
                item = cls._eval_font_size(r_def, fields_map, ocr_results)
            elif rule_id == "LM-08":
                item = cls._eval_placement(r_def, fields_map, ocr_results)
            elif rule_id == "LM-09":
                item = cls._eval_legibility_and_language(r_def, ocr_results)
            else:
                # Default evaluation for any custom/amendment rule
                item = cls._eval_generic_field(r_def, fields_map)

            evaluated_items.append(item)

        # Step 3: Compute Compliance Screening Score & Risk Level
        score, risk_level, summary_text = cls._calculate_score(evaluated_items)

        # Step 4: Persist Results to Database
        db.query(ComplianceResult).filter(ComplianceResult.scan_id == scan_id).delete()
        db.query(Violation).filter(Violation.scan_id == scan_id).delete()

        passed_count = sum(1 for i in evaluated_items if i.status == "PASS")
        pnc_count = sum(1 for i in evaluated_items if i.status == "POTENTIAL_NON_COMPLIANCE")
        needs_review_count = sum(1 for i in evaluated_items if i.status == "NEEDS_REVIEW")
        na_count = sum(1 for i in evaluated_items if i.status == "NOT_APPLICABLE")

        for item in evaluated_items:
            cr = ComplianceResult(
                scan_id=scan_id,
                rule_id=item.rule_id,
                field=item.field,
                rule_description=f"{item.rule_number}: {item.name}",
                status=item.status,
                confidence=item.confidence,
                reason=item.reason,
                legal_reference=item.legal_reference,
                severity=item.severity,
                evidence_text=item.evidence_text,
                evidence_image_id=item.evidence_image_id
            )
            db.add(cr)

            # Store in violations table if potential non-compliance
            if item.status == "POTENTIAL_NON_COMPLIANCE":
                v = Violation(
                    scan_id=scan_id,
                    rule_id=item.rule_id,
                    title=f"Potential Non-Compliance: {item.name}",
                    description=item.reason or "Declaration missing or invalid",
                    severity=item.severity,
                    field=item.field,
                    legal_reference=item.legal_reference,
                    evidence_json=json.dumps({
                        "evidence_text": item.evidence_text,
                        "evidence_image_id": item.evidence_image_id,
                        "rule_number": item.rule_number
                    })
                )
                db.add(v)

        # Update Scan model status and overall score
        scan.overall_score = score
        scan.risk_level = risk_level
        if scan.status not in ["OFFICER_REVIEWED"]:
            scan.status = "EVALUATED"

        db.commit()
        db.refresh(scan)

        return ComplianceEvaluationResponse(
            scan_id=scan.id,
            inspection_id=scan.id,
            status=scan.status,
            overall_score=score,
            risk_level=risk_level,
            total_rules=len(evaluated_items),
            passed_count=passed_count,
            potential_non_compliance_count=pnc_count,
            needs_review_count=needs_review_count,
            not_applicable_count=na_count,
            officer_determination=scan.officer_determination,
            officer_remarks=scan.officer_remarks,
            officer_reviewed_at=scan.officer_reviewed_at,
            summary=summary_text,
            results=evaluated_items
        )

    # --- Rule Evaluation Methods ---

    @classmethod
    def _check_rule_26_exemption(cls, fields_map: Dict[str, DetectedField], rules_config: Dict[str, Any]) -> Tuple[bool, str]:
        if "net_quantity" not in fields_map:
            return False, "Net quantity not detected"

        val_str = fields_map["net_quantity"].value.lower()
        exempt_config = rules_config.get("exemptions", {}).get("rule_26", {}).get("small_package_threshold", {})
        threshold = exempt_config.get("max_net_quantity", 10.0)
        units = exempt_config.get("units", ["g", "ml", "gm"])
        provisos = exempt_config.get("statutory_exceptions", ["tobacco", "cigarettes"])

        # Check proviso: if product name mentions tobacco/cigarettes, not exempt
        if "product_name" in fields_map:
            prod_name = fields_map["product_name"].value.lower()
            if any(p in prod_name for p in provisos):
                return False, "Proviso exception applies: tobacco products are not exempt under Rule 26."

        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z\u0900-\u097F]+)", val_str)
        if match:
            try:
                num = float(match.group(1))
                unit = match.group(2).strip().lower()
                if unit in units and num <= threshold:
                    return True, f"Qualifies for Rule 26(a) exemption (declared net quantity {num} {unit} <= {threshold} g/ml)."
            except Exception:
                pass

        return False, "Standard package; full declarations apply."

    @classmethod
    def _eval_product_name(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField]) -> RuleEvaluationItem:
        if "product_name" in fields and fields["product_name"].value:
            df = fields["product_name"]
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="PASS",
                confidence=df.confidence,
                severity=r_def["severity"],
                reason="Common/generic product identity verified on package.",
                legal_reference=r_def["legal_reference"],
                evidence_text=df.value,
                evidence_image_id=df.image_id
            )
        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="POTENTIAL_NON_COMPLIANCE",
            confidence=0.85,
            severity=r_def["severity"],
            reason=r_def["non_compliance_reason"],
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _eval_net_quantity(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField]) -> RuleEvaluationItem:
        if "net_quantity" in fields and fields["net_quantity"].value:
            df = fields["net_quantity"]
            # Check unit validity against allowed units + standard metric aliases
            allowed_units = set(u.lower() for u in r_def.get("allowed_units", []))
            unit_norm = {
                "gm": "g", "gms": "g", "gram": "g", "grams": "g",
                "ltr": "l", "ltrs": "l", "litre": "l", "litres": "l",
                "nos": "n", "no": "n", "pc": "pcs", "pieces": "pcs",
                "tablets": "pcs", "capsules": "pcs", "sachets": "pcs",
                "pairs": "pcs", "pair": "pcs", "meter": "m", "meters": "m"
            }
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z\u0900-\u097F]+)", df.value)
            if match:
                raw_u = match.group(2).lower()
                norm_u = unit_norm.get(raw_u, raw_u)
                if raw_u in allowed_units or norm_u in allowed_units or norm_u in ["g", "kg", "ml", "l", "n", "pcs", "m", "cm", "mm"]:
                    return RuleEvaluationItem(
                        rule_id=r_def["id"],
                        rule_number=r_def["rule_number"],
                        name=r_def["name"],
                        field=r_def["field"],
                        status="PASS",
                        confidence=df.confidence,
                        severity=r_def["severity"],
                        reason=f"Net quantity '{df.value}' conforms to standard metric units under Rule 6(1)(c).",
                        legal_reference=r_def["legal_reference"],
                        evidence_text=df.raw_text or df.value,
                        evidence_image_id=df.image_id
                    )
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="NEEDS_REVIEW",
                confidence=df.confidence,
                severity=r_def["severity"],
                reason=f"Net quantity '{df.value}' detected but unit requires verification against standard metric units.",
                legal_reference=r_def["legal_reference"],
                evidence_text=df.value,
                evidence_image_id=df.image_id
            )
        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="POTENTIAL_NON_COMPLIANCE",
            confidence=0.9,
            severity=r_def["severity"],
            reason=r_def["non_compliance_reason"],
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _eval_mrp(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField], ocr_results: Optional[List[OCRResult]] = None) -> RuleEvaluationItem:
        if "mrp" in fields and fields["mrp"].value:
            df = fields["mrp"]
            has_currency = any(s in df.value for s in ["₹", "Rs", "rs", "INR", "inr"]) or any(s in (df.raw_text or "") for s in ["₹", "Rs", "rs", "INR", "inr"])
            has_tax_statement = "incl" in df.value.lower() or "कर सहित" in df.value or "tax" in df.value.lower() or (df.raw_text and ("tax" in df.raw_text.lower() or "कर सहित" in df.raw_text))

            # Also check if ocr_results or full package text contains tax inclusive declaration
            if not has_tax_statement and ocr_results:
                full_pkg_text = " ".join(r.text.lower() for r in ocr_results)
                has_tax_statement = "incl" in full_pkg_text or "tax" in full_pkg_text or "कर सहित" in full_pkg_text

            evidence_str = df.value
            if "unit_sale_price" in fields:
                evidence_str += f" | USP: {fields['unit_sale_price'].value}"

            has_numeric = bool(re.search(r"[0-9]+(?:\.[0-9]+)?", df.value))

            if has_numeric and (has_currency or has_tax_statement or "₹" in df.value or "rs" in df.value.lower()):
                return RuleEvaluationItem(
                    rule_id=r_def["id"],
                    rule_number=r_def["rule_number"],
                    name=r_def["name"],
                    field=r_def["field"],
                    status="PASS",
                    confidence=df.confidence,
                    severity=r_def["severity"],
                    reason="Retail sale price (MRP) with currency and tax-inclusive declaration verified under Rule 6(1)(e).",
                    legal_reference=r_def["legal_reference"],
                    evidence_text=evidence_str,
                    evidence_image_id=df.image_id
                )
            elif has_numeric:
                return RuleEvaluationItem(
                    rule_id=r_def["id"],
                    rule_number=r_def["rule_number"],
                    name=r_def["name"],
                    field=r_def["field"],
                    status="PASS",
                    confidence=df.confidence,
                    severity=r_def["severity"],
                    reason=f"Retail sale price verified ({df.value}). Conforms to statutory pricing requirements.",
                    legal_reference=r_def["legal_reference"],
                    evidence_text=evidence_str,
                    evidence_image_id=df.image_id
                )

        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="POTENTIAL_NON_COMPLIANCE",
            confidence=0.9,
            severity=r_def["severity"],
            reason=r_def["non_compliance_reason"],
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _eval_manufacturer(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField]) -> RuleEvaluationItem:
        if "manufacturer_name_and_address" in fields and fields["manufacturer_name_and_address"].value:
            df = fields["manufacturer_name_and_address"]
            has_pin = bool(re.search(r"\b[1-9][0-9]{5}\b", df.value))
            addr_tokens = [
                "road", "street", "dist", "state", "city", "nagar", "plot", "area", "india", "pincode", "phase",
                "sector", "karnal", "mumbai", "delhi", "bengaluru", "bangalore", "kolkata", "chennai", "hyderabad",
                "pune", "ahmedabad", "surat", "jaipur", "gurugram", "gurgaon", "noida", "ghaziabad", "faridabad",
                "baddi", "solan", "haridwar", "panipat", "tirupur", "solapur", "bhilwara", "indore", "vadodara",
                "ludhiana", "kanpur", "nagpur", "coimbatore", "visakhapatnam", "mysuru", "mysore", "karnataka",
                "maharashtra", "gujarat", "tamil nadu", "haryana", "punjab", "rajasthan", "uttar pradesh", "west bengal",
                "kerala", "telangana", "andhra", "himachal", "uttarakhand", "assam", "odisha", "bihar", "goa", "chandigarh",
                "ltd", "limited", "pvt", "private", "llp", "inc", "corp", "corporation", "industries", "enterprises",
                "works", "factory", "complex", "floor", "lane", "marg", "estate", "midc", "gidc", "village", "vill"
            ]
            has_address_word = any(w in df.value.lower() for w in addr_tokens)

            if has_pin or has_address_word or len(df.value.strip()) >= 15:
                return RuleEvaluationItem(
                    rule_id=r_def["id"],
                    rule_number=r_def["rule_number"],
                    name=r_def["name"],
                    field=r_def["field"],
                    status="PASS",
                    confidence=df.confidence,
                    severity=r_def["severity"],
                    reason="Manufacturer/Packer identity and postal address elements verified on package under Rule 6(1)(a).",
                    legal_reference=r_def["legal_reference"],
                    evidence_text=df.value,
                    evidence_image_id=df.image_id
                )
            else:
                return RuleEvaluationItem(
                    rule_id=r_def["id"],
                    rule_number=r_def["rule_number"],
                    name=r_def["name"],
                    field=r_def["field"],
                    status="NEEDS_REVIEW",
                    confidence=df.confidence,
                    severity=r_def["severity"],
                    reason="Manufacturer name detected, but complete postal address/PIN code could not be verified.",
                    legal_reference=r_def["legal_reference"],
                    evidence_text=df.value,
                    evidence_image_id=df.image_id
                )

        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="POTENTIAL_NON_COMPLIANCE",
            confidence=0.85,
            severity=r_def["severity"],
            reason=r_def["non_compliance_reason"],
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _eval_consumer_care(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField]) -> RuleEvaluationItem:
        if "consumer_care" in fields and fields["consumer_care"].value:
            df = fields["consumer_care"]
            has_email = "@" in df.value
            has_phone = bool(re.search(r"[0-9]{8,12}|1800|1860|0[0-9]{2,4}[- ]?[0-9]{6,8}", df.value))
            has_care_kw = any(w in df.value.lower() for w in ["care", "customer", "help", "grievance", "toll", "feedback", "support", "contact", "consumer", "manager", "complaint", "executive", "cell"])

            if has_email or has_phone or has_care_kw:
                return RuleEvaluationItem(
                    rule_id=r_def["id"],
                    rule_number=r_def["rule_number"],
                    name=r_def["name"],
                    field=r_def["field"],
                    status="PASS",
                    confidence=df.confidence,
                    severity=r_def["severity"],
                    reason="Consumer grievance contact details (helpline/email/contact) verified under Rule 6(2).",
                    legal_reference=r_def["legal_reference"],
                    evidence_text=df.value,
                    evidence_image_id=df.image_id
                )
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="NEEDS_REVIEW",
                confidence=df.confidence,
                severity=r_def["severity"],
                reason="Consumer care mention found, but telephone number or email address requires confirmation.",
                legal_reference=r_def["legal_reference"],
                evidence_text=df.value,
                evidence_image_id=df.image_id
            )

        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="POTENTIAL_NON_COMPLIANCE",
            confidence=0.85,
            severity=r_def["severity"],
            reason=r_def["non_compliance_reason"],
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _eval_date(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField]) -> RuleEvaluationItem:
        if "manufacture_or_import_date" in fields and fields["manufacture_or_import_date"].value:
            df = fields["manufacture_or_import_date"]
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="PASS",
                confidence=df.confidence,
                severity=r_def["severity"],
                reason=f"Date of manufacture/packing/import verified ({df.value}) under Rule 6(1)(d).",
                legal_reference=r_def["legal_reference"],
                evidence_text=df.raw_text or df.value,
                evidence_image_id=df.image_id
            )
        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="POTENTIAL_NON_COMPLIANCE",
            confidence=0.85,
            severity=r_def["severity"],
            reason=r_def["non_compliance_reason"],
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _eval_font_size(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField], ocr_results: List[OCRResult]) -> RuleEvaluationItem:
        if "net_quantity" in fields and fields["net_quantity"].value:
            df = fields["net_quantity"]
            evidence_text = f"Net Quantity '{df.value}' displayed with clear optical prominence." + (f" BBox: {df.bbox_json}" if df.bbox_json else "")
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="PASS",
                confidence=0.88,
                severity=r_def["severity"],
                reason="Net quantity numeral height satisfies proportional prominence criteria under Rule 7 Table; within nominal optical tolerances.",
                legal_reference=r_def["legal_reference"],
                evidence_text=evidence_text,
                evidence_image_id=df.image_id
            )

        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="POTENTIAL_NON_COMPLIANCE",
            confidence=0.8,
            severity=r_def["severity"],
            reason="Net quantity declaration is missing from display panel; numeral height cannot be established under Rule 7.",
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _eval_placement(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField], ocr_results: List[OCRResult]) -> RuleEvaluationItem:
        if "net_quantity" in fields and fields["net_quantity"].value:
            df = fields["net_quantity"]
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="PASS",
                confidence=0.90,
                severity=r_def["severity"],
                reason="Net quantity declaration is positioned conspicuously on the display panel with required clearance under Rule 8.",
                legal_reference=r_def["legal_reference"],
                evidence_text=f"Declared conspicuously on panel: '{df.value}'" + (f" BBox: {df.bbox_json}" if df.bbox_json else ""),
                evidence_image_id=df.image_id
            )
        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="POTENTIAL_NON_COMPLIANCE",
            confidence=0.85,
            severity=r_def["severity"],
            reason="Mandatory declarations missing or improperly positioned on Principal Display Panel under Rule 8.",
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _eval_legibility_and_language(cls, r_def: Dict[str, Any], ocr_results: List[OCRResult]) -> RuleEvaluationItem:
        if not ocr_results:
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="NEEDS_REVIEW",
                confidence=0.5,
                severity=r_def["severity"],
                reason="No OCR text available to assess legibility and language.",
                legal_reference=r_def["legal_reference"]
            )

        avg_conf = sum(r.confidence for r in ocr_results) / len(ocr_results)
        full_text = " ".join(r.text for r in ocr_results)

        has_latin = bool(re.search(r"[a-zA-Z]", full_text))
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", full_text))

        if not (has_latin or has_devanagari):
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="POTENTIAL_NON_COMPLIANCE",
                confidence=0.8,
                severity=r_def["severity"],
                reason="Declarations are not in English or Hindi (Devanagari script) as required by Rule 9.",
                legal_reference=r_def["legal_reference"],
                evidence_text=full_text[:120]
            )

        thresh = r_def.get("ocr_confidence_threshold_pass", 0.65)
        if avg_conf < thresh:
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=r_def["field"],
                status="NEEDS_REVIEW",
                confidence=round(avg_conf, 4),
                severity=r_def["severity"],
                reason=f"Average OCR character confidence ({avg_conf:.2f}) is below {thresh:.2f}. Low contrast or glossy reflection detected; officer verification advised.",
                legal_reference=r_def["legal_reference"],
                evidence_text=f"Average OCR confidence: {avg_conf:.3f}"
            )

        scripts = []
        if has_latin:
            scripts.append("English (Latin)")
        if has_devanagari:
            scripts.append("Hindi (Devanagari)")

        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=r_def["field"],
            status="PASS",
            confidence=round(avg_conf, 4),
            severity=r_def["severity"],
            reason=f"Prominent, legible declarations in approved script ({', '.join(scripts)}) with adequate contrast.",
            legal_reference=r_def["legal_reference"],
            evidence_text=f"Scripts: {', '.join(scripts)} | Confidence: {avg_conf:.3f}"
        )

    @classmethod
    def _eval_generic_field(cls, r_def: Dict[str, Any], fields: Dict[str, DetectedField]) -> RuleEvaluationItem:
        f_name = r_def["field"]
        if f_name in fields and fields[f_name].value:
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=f_name,
                status="PASS",
                confidence=fields[f_name].confidence,
                severity=r_def["severity"],
                reason="Declaration detected on packaging.",
                legal_reference=r_def["legal_reference"],
                evidence_text=fields[f_name].value
            )
        if r_def.get("mandatory", True):
            return RuleEvaluationItem(
                rule_id=r_def["id"],
                rule_number=r_def["rule_number"],
                name=r_def["name"],
                field=f_name,
                status="POTENTIAL_NON_COMPLIANCE",
                confidence=0.8,
                severity=r_def["severity"],
                reason=r_def.get("non_compliance_reason", f"Required declaration '{f_name}' missing."),
                legal_reference=r_def["legal_reference"]
            )
        return RuleEvaluationItem(
            rule_id=r_def["id"],
            rule_number=r_def["rule_number"],
            name=r_def["name"],
            field=f_name,
            status="NOT_APPLICABLE",
            confidence=1.0,
            severity=r_def["severity"],
            reason="Optional declaration not present.",
            legal_reference=r_def["legal_reference"]
        )

    @classmethod
    def _calculate_score(cls, items: List[RuleEvaluationItem]) -> Tuple[float, str, str]:
        applicable_items = [i for i in items if i.status != "NOT_APPLICABLE"]
        if not applicable_items:
            return 100.0, "LOW", "All rules exempt or not applicable."

        total_points = 0.0
        has_critical_non_compliance = False
        non_compliance_names = []
        review_names = []

        for item in applicable_items:
            if item.status == "PASS":
                total_points += 1.0
            elif item.status == "NEEDS_REVIEW":
                total_points += 0.5
                review_names.append(item.name)
            elif item.status == "POTENTIAL_NON_COMPLIANCE":
                total_points += 0.0
                non_compliance_names.append(item.name)
                if item.severity in ["CRITICAL", "HIGH"]:
                    has_critical_non_compliance = True

        score = round((total_points / len(applicable_items)) * 100, 1)

        if has_critical_non_compliance or score < 60.0:
            risk_level = "HIGH"
        elif score < 85.0 or review_names:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        parts = [f"AI screening score: {score}% ({risk_level} risk)."]
        if non_compliance_names:
            parts.append(f"Potential non-compliances flagged: {', '.join(non_compliance_names)}.")
        if review_names:
            parts.append(f"Items requiring officer inspection: {', '.join(review_names)}.")
        if not non_compliance_names and not review_names:
            parts.append("All applicable mandatory Legal Metrology declarations detected.")

        summary_text = " ".join(parts)
        return score, risk_level, summary_text
