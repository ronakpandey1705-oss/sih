import pytest


def test_get_ruleset_configuration(client):
    response = client.get("/api/compliance/rules")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert data["total_rules"] == 10
    rule_ids = [r["id"] for r in data["rules"]]
    assert "LM-01" in rule_ids
    assert "LM-02" in rule_ids
    assert "LM-03" in rule_ids
    assert "LM-04" in rule_ids
    assert "LM-05" in rule_ids
    assert "LM-06" in rule_ids
    assert "LM-07" in rule_ids
    assert "LM-08" in rule_ids
    assert "LM-09" in rule_ids
    assert "LM-10" in rule_ids
    assert "schedules" in data
    assert "amendments" in data


def test_inspection_extract_fields_and_evaluate_api(client):
    import io
    from PIL import Image
    from tests.conftest import TestingSessionLocal
    from app.models.ocr_result import OCRResult

    # 1. Create official inspection
    create_resp = client.post("/api/inspections/", json={
        "barcode": "8901234567890",
        "officer_id": "LM-INSP-2026-901",
        "establishment_name": "Mega Retail Mart",
        "inspection_location": "Pune, Maharashtra"
    })
    assert create_resp.status_code == 201
    insp_id = create_resp.json()["inspection_id"]

    # 2. Upload image
    img_buf = io.BytesIO()
    Image.new("RGB", (300, 200), color=(250, 250, 250)).save(img_buf, format="JPEG")
    img_buf.seek(0)
    up_resp = client.post(f"/api/inspections/{insp_id}/images", files={"file": ("sample.jpg", img_buf, "image/jpeg")})
    img_id = up_resp.json()["image_id"]

    # 3. Inject OCR results
    db = TestingSessionLocal()
    try:
        sample_ocr = [
            "DemoBakes Choco Delight Biscuits",
            "Net Weight: 200 g",
            "MRP Rs. 50.00 (incl. of all taxes)",
            "Unit Sale Price Rs. 0.25 / g",
            "Mfg by Demo Food Corp, Plot 4, Pune 411001",
            "Consumer Care Cell: 1800-222-333, care@demofood.com",
            "Pkd: 09/2026"
        ]
        for i, line in enumerate(sample_ocr):
            db.add(OCRResult(
                scan_id=insp_id,
                image_id=img_id,
                text=line,
                confidence=0.96,
                line_order=i
            ))
        db.commit()
    finally:
        db.close()

    # 4. Call /api/inspections/{id}/extract-fields
    ext_resp = client.post(f"/api/inspections/{insp_id}/extract-fields")
    assert ext_resp.status_code == 200
    ext_data = ext_resp.json()
    assert ext_data["total_fields"] >= 6
    extracted_names = [f["field_name"] for f in ext_data["fields"]]
    assert "net_quantity" in extracted_names
    assert "mrp" in extracted_names
    assert "manufacturer_name_and_address" in extracted_names

    # 5. Call /api/inspections/{id}/evaluate
    eval_resp = client.post(f"/api/inspections/{insp_id}/evaluate")
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["status"] in ["EVALUATED", "OFFICER_REVIEWED"]
    assert eval_data["overall_score"] > 70.0
    assert eval_data["total_rules"] == 10
    assert eval_data["passed_count"] >= 6

    # 6. Call /api/inspections/{id}/compliance
    comp_resp = client.get(f"/api/inspections/{insp_id}/compliance")
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["overall_score"] == eval_data["overall_score"]
    assert len(comp_data["results"]) == 10

    # 7. Officer reviews evidence and completes inspection
    review_resp = client.post(f"/api/inspections/{insp_id}/review", json={
        "officer_determination": "COMPLIANT",
        "officer_remarks": "All mandatory Legal Metrology declarations verified on retail package.",
        "officer_id": "LM-INSP-2026-901"
    })
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "OFFICER_REVIEWED"
    assert review_resp.json()["officer_determination"] == "COMPLIANT"
