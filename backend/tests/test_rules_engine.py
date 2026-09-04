import pytest
from app.models.scan import Scan
from app.models.detected_field import DetectedField
from app.models.ocr_result import OCRResult
from app.services.compliance.rules_engine import RulesEngine
from tests.conftest import TestingSessionLocal


def test_rules_engine_all_compliant(client):
    resp = client.post("/api/inspections/", json={"establishment_name": "Compliance Store"})
    insp_id = resp.json()["inspection_id"]

    db = TestingSessionLocal()
    try:
        fields = [
            ("product_name", "Supreme Wheat Flour"),
            ("net_quantity", "5 kg"),
            ("mrp", "₹ 240.00 (incl. of all taxes)"),
            ("unit_sale_price", "₹ 48.00 / kg"),
            ("manufacturer_name_and_address", "Agro Millers Ltd, Sector 5, Karnal, Haryana 132001"),
            ("consumer_care", "Tel: 1800-999-8888, Email: support@agromillers.com"),
            ("manufacture_or_import_date", "07/2026"),
        ]
        for fn, val in fields:
            df = DetectedField(
                scan_id=insp_id,
                field_name=fn,
                value=val,
                confidence=0.95,
                bbox_json='{"bbox": [10, 10, 100, 20]}'
            )
            db.add(df)

        ocr = OCRResult(scan_id=insp_id, image_id="img1", text="Sample OCR English Text", confidence=0.92)
        db.add(ocr)
        db.commit()

        result = RulesEngine.evaluate_scan(insp_id, db)
        assert result.overall_score >= 80.0
        assert result.potential_non_compliance_count == 0
        assert result.passed_count >= 6  # LM-01 to LM-06 should pass

        results_by_id = {r.rule_id: r for r in result.results}
        assert results_by_id["LM-01"].status == "PASS"
        assert results_by_id["LM-02"].status == "PASS"
        assert results_by_id["LM-03"].status == "PASS"
        assert results_by_id["LM-04"].status == "PASS"
        assert results_by_id["LM-05"].status == "PASS"
        assert results_by_id["LM-06"].status == "PASS"

    finally:
        db.close()


def test_rules_engine_missing_mandatory_declarations(client):
    resp = client.post("/api/inspections/", json={})
    insp_id = resp.json()["inspection_id"]

    db = TestingSessionLocal()
    try:
        # Only net quantity is present; MRP, manufacturer, date, consumer care missing
        df = DetectedField(
            scan_id=insp_id,
            field_name="net_quantity",
            value="100 g",
            confidence=0.95
        )
        db.add(df)
        ocr = OCRResult(scan_id=insp_id, image_id="img1", text="Net Qty: 100 g", confidence=0.90)
        db.add(ocr)
        db.commit()

        result = RulesEngine.evaluate_scan(insp_id, db)
        assert result.risk_level == "HIGH"
        assert result.potential_non_compliance_count >= 3

        results_by_id = {r.rule_id: r for r in result.results}
        assert results_by_id["LM-02"].status == "PASS"
        assert results_by_id["LM-03"].status == "POTENTIAL_NON_COMPLIANCE"
        assert results_by_id["LM-04"].status == "POTENTIAL_NON_COMPLIANCE"
        assert results_by_id["LM-05"].status == "POTENTIAL_NON_COMPLIANCE"

    finally:
        db.close()


def test_rules_engine_rule_26_exemption(client):
    resp = client.post("/api/inspections/", json={})
    insp_id = resp.json()["inspection_id"]

    db = TestingSessionLocal()
    try:
        # 5 g small package (qualifies for Rule 26 exemption)
        df1 = DetectedField(scan_id=insp_id, field_name="product_name", value="Instant Coffee Sachet", confidence=0.9)
        df2 = DetectedField(scan_id=insp_id, field_name="net_quantity", value="5 g", confidence=0.95)
        df3 = DetectedField(scan_id=insp_id, field_name="mrp", value="₹ 2.00 (incl. of all taxes)", confidence=0.95)
        df4 = DetectedField(scan_id=insp_id, field_name="manufacturer_name_and_address", value="Coffee India Ltd, Bangalore 560001", confidence=0.9)
        for d in [df1, df2, df3, df4]:
            db.add(d)

        ocr = OCRResult(scan_id=insp_id, image_id="img1", text="Coffee Sachet Net: 5g", confidence=0.92)
        db.add(ocr)
        db.commit()

        result = RulesEngine.evaluate_scan(insp_id, db)
        results_by_id = {r.rule_id: r for r in result.results}

        # LM-10 should pass (exemption applies)
        assert results_by_id["LM-10"].status == "PASS"

        # LM-07 and LM-08 should be NOT_APPLICABLE for <= 10g small packages
        assert results_by_id["LM-07"].status == "NOT_APPLICABLE"
        assert results_by_id["LM-08"].status == "NOT_APPLICABLE"

    finally:
        db.close()
