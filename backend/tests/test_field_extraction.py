import pytest
from app.models.scan import Scan
from app.models.ocr_result import OCRResult
from app.models.image import UploadedImage
from app.services.extraction.field_extractor import FieldExtractor


def test_field_extraction_full_sample(client):
    # Create an inspection
    resp = client.post("/api/inspections/", json={
        "establishment_name": "Testing Mart",
        "inspection_location": "Mumbai"
    })
    insp_id = resp.json()["inspection_id"]

    # Post an image
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (100, 100)).save(buf, format="JPEG")
    buf.seek(0)
    img_resp = client.post(f"/api/inspections/{insp_id}/images", files={"file": ("pack.jpg", buf, "image/jpeg")})
    img_id = img_resp.json()["image_id"]

    # Inject realistic OCR lines into database directly via test override or session
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        sample_lines = [
            "Demo Crunchy Cookies",
            "Net Qty: 250 g",
            "M.R.P. Rs. 45.00 (incl. of all taxes)",
            "Unit Sale Price Rs. 0.18 / g",
            "Mfg by Demo Foods Pvt Ltd",
            "Plot 12, Industrial Area, Andheri, Mumbai 400093",
            "Customer Care: 1800-123-4567, email: care@demofoods.com",
            "Mfg Date: 08/2026",
            "Dimensions: 10 cm x 5 cm x 2 cm"
        ]
        for idx, txt in enumerate(sample_lines):
            r = OCRResult(
                scan_id=insp_id,
                image_id=img_id,
                text=txt,
                confidence=0.98,
                bbox_json='{"bbox": [10, 10, 200, 30]}',
                line_order=idx
            )
            db.add(r)
        db.commit()

        # Run extraction
        extracted = FieldExtractor.extract_from_scan(insp_id, db)
        extracted_map = {f.field_name: f.value for f in extracted}

        assert "product_name" in extracted_map
        assert "Crunchy" in extracted_map["product_name"]

        assert "net_quantity" in extracted_map
        assert "250 g" in extracted_map["net_quantity"]

        assert "mrp" in extracted_map
        assert "45.00" in extracted_map["mrp"]

        assert "unit_sale_price" in extracted_map
        assert "0.18" in extracted_map["unit_sale_price"]

        assert "manufacturer_name_and_address" in extracted_map
        assert "Demo Foods" in extracted_map["manufacturer_name_and_address"]
        assert "400093" in extracted_map["manufacturer_name_and_address"]

        assert "consumer_care" in extracted_map
        assert "1800-123-4567" in extracted_map["consumer_care"]
        assert "care@demofoods.com" in extracted_map["consumer_care"]

        assert "manufacture_or_import_date" in extracted_map
        assert "08/2026" in extracted_map["manufacture_or_import_date"]

        assert "dimensions" in extracted_map
        assert "10 cm x 5 cm x 2 cm" in extracted_map["dimensions"]

    finally:
        db.close()


def test_field_extraction_hindi_devanagari(client):
    resp = client.post("/api/inspections/", json={})
    insp_id = resp.json()["inspection_id"]

    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    try:
        sample_lines = [
            "स्वादिष्ट नमकीन",
            "शुद्ध मात्रा : 500 ग्राम",
            "अधिकतम खुदरा मूल्य ₹ 90.00 कर सहित",
            "निर्माता : भारत फूड्स, नई दिल्ली 110001",
            "उपभोक्ता सेवा : 9876543210"
        ]
        for idx, txt in enumerate(sample_lines):
            r = OCRResult(
                scan_id=insp_id,
                image_id="dummy-img",
                text=txt,
                confidence=0.95,
                line_order=idx
            )
            db.add(r)
        db.commit()

        extracted = FieldExtractor.extract_from_scan(insp_id, db)
        extracted_map = {f.field_name: f.value for f in extracted}

        assert "net_quantity" in extracted_map
        assert "500 ग्राम" in extracted_map["net_quantity"]
        assert "mrp" in extracted_map
        assert "90.00" in extracted_map["mrp"]
        assert "manufacturer_name_and_address" in extracted_map
        assert "भारत फूड्स" in extracted_map["manufacturer_name_and_address"]

    finally:
        db.close()
