from app.database import get_db
from app.models.image import UploadedImage
from app.models.ocr_result import OCRResult

def test_uncataloged_product_inspection_detected_and_missing(client):
    # Create scan session via client API
    s_resp = client.post("/api/scans", json={"barcode": "8909999999999"})
    assert s_resp.status_code == 201
    scan_id = s_resp.json()["scan_id"]

    # Use test db session from dependency override
    db = next(client.app.dependency_overrides[get_db]())
    try:
        img = UploadedImage(
            id="test-img-uncataloged",
            scan_id=scan_id,
            filename="front_panel.jpg",
            original_path="/tmp/fake.jpg",
            file_size=1024,
            mime_type="image/jpeg"
        )
        db.add(img)
        db.commit()

        # Add OCR lines representing a front panel of a real uncataloged product
        ocr_lines = [
            "GoodDay Cashew Cookies",
            "Rich Butter and Cashew Biscuits",
            "Net Wt: 100g",
            "MRP Rs. 20.00 (Incl. of all taxes)",
            "USP Rs. 0.20 / g"
        ]
        for idx, line in enumerate(ocr_lines):
            r = OCRResult(
                scan_id=scan_id,
                image_id=img.id,
                text=line,
                confidence=0.96,
                line_order=idx,
                bbox_json="[10, 10, 200, 40]"
            )
            db.add(r)
        db.commit()
    finally:
        db.close()

    # Run analyze
    resp = client.post(f"/api/scans/{scan_id}/analyze")
    assert resp.status_code == 200
    data = resp.json()

    # Verify detected declarations
    detected = {d["field"]: d["value"] for d in data.get("detected_declarations", [])}
    assert "net_quantity" in detected
    assert "100" in detected["net_quantity"]
    assert "mrp" in detected
    assert "20" in detected["mrp"]

    # Verify missing declarations (back panel declarations not on front photo)
    missing_fields = [m["field"] for m in data.get("missing_declarations", [])]
    assert "manufacturer_name_and_address" in missing_fields
    assert "consumer_care" in missing_fields

    # Verify rules summary passes for net quantity and MRP
    rules_status = {r["rule_id"]: r["status"] for r in data.get("rules_summary", [])}
    assert rules_status["LM-02"] == "PASS"  # Net quantity passes
    assert rules_status["LM-03"] == "PASS"  # MRP passes
