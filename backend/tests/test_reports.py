import io
import pytest
from PIL import Image
from tests.conftest import TestingSessionLocal
from app.models.ocr_result import OCRResult


def _setup_inspection_with_ocr(client):
    # Create inspection
    resp = client.post("/api/inspections/", json={
        "barcode": "8901234567890",
        "officer_id": "LM-OFFICER-777",
        "establishment_name": "Godrej Fresh Mart, Powai",
        "inspection_location": "Powai, Mumbai, Maharashtra"
    })
    insp_id = resp.json()["inspection_id"]

    # Upload packaging image
    img_buf = io.BytesIO()
    Image.new("RGB", (250, 250), color=(240, 240, 240)).save(img_buf, format="JPEG")
    img_buf.seek(0)
    up = client.post(f"/api/inspections/{insp_id}/images", files={"file": ("packaging.jpg", img_buf, "image/jpeg")})
    img_id = up.json()["image_id"]

    # Inject OCR results
    db = TestingSessionLocal()
    try:
        lines = [
            "DemoBakes Choco Delight Biscuits",
            "Net Qty: 200 g",
            "MRP Rs. 50.00 (incl. of all taxes)",
            "Unit Sale Price Rs. 0.25 / g",
            "Mfg by Demo Foods Pvt Ltd, Plot 10, MIDC, Mumbai 400093",
            "Consumer Care: 1800-444-555, email: care@demobakes.com",
            "Mfg Date: 08/2026"
        ]
        for i, line in enumerate(lines):
            db.add(OCRResult(
                scan_id=insp_id,
                image_id=img_id,
                text=line,
                confidence=0.98,
                bbox_json='{"bbox": [10, 20, 200, 40]}',
                line_order=i
            ))
        db.commit()
    finally:
        db.close()

    return insp_id


def test_evidence_collation_endpoint(client):
    insp_id = _setup_inspection_with_ocr(client)

    # Call /api/inspections/{id}/extract-fields first
    client.post(f"/api/inspections/{insp_id}/extract-fields")
    client.post(f"/api/inspections/{insp_id}/evaluate")

    resp = client.get(f"/api/inspections/{insp_id}/evidence")
    assert resp.status_code == 200
    ev_data = resp.json()

    assert ev_data["inspection_id"] == insp_id
    assert ev_data["officer_id"] == "LM-OFFICER-777"
    assert ev_data["images_count"] >= 1
    assert ev_data["ocr_items_count"] >= 7
    assert ev_data["detected_fields_count"] >= 5
    assert ev_data["compliance_rules_count"] == 10
    assert "discrepancies" in ev_data


def test_discrepancies_endpoint(client):
    insp_id = _setup_inspection_with_ocr(client)
    client.post(f"/api/inspections/{insp_id}/extract-fields")

    resp = client.get(f"/api/inspections/{insp_id}/discrepancies")
    assert resp.status_code == 200
    disc = resp.json()
    assert disc["barcode"] == "8901234567890"
    assert disc["has_catalog_baseline"] is True
    assert disc["total_discrepancies"] == 0  # Expected 200g & Rs 50 matches catalog


def test_unified_analyze_endpoint(client):
    insp_id = _setup_inspection_with_ocr(client)

    # Call one-shot analyze
    resp = client.post(f"/api/inspections/{insp_id}/analyze")
    assert resp.status_code == 200
    data = resp.json()

    assert data["inspection_id"] == insp_id
    assert data["overall_score"] >= 80.0
    assert data["fields_extracted_count"] >= 5
    assert data["rules_evaluated_count"] == 10
    assert data["passed_rules_count"] >= 6
    assert len(data["rules_summary"]) == 10


def test_generate_report_and_download_pdf(client):
    insp_id = _setup_inspection_with_ocr(client)

    # 1. Officer submits review
    client.post(f"/api/inspections/{insp_id}/review", json={
        "officer_determination": "COMPLIANT",
        "officer_remarks": "Packaged commodity conforms to Legal Metrology Rule 6 requirements.",
        "officer_id": "LM-OFFICER-777"
    })

    # 2. Generate report
    rep_resp = client.post(f"/api/inspections/{insp_id}/report", json={
        "officer_notes": "Official surveillance inspection",
        "authority_name": "Maharashtra Legal Metrology Dept",
        "authority_jurisdiction": "Mumbai Suburban"
    })
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert "report_number" in rep_data
    assert rep_data["report_number"].startswith("LM-INSP-")
    assert rep_data["status"] == "GENERATED"
    assert rep_data["pdf_download_url"] is not None
    assert "Legal Metrology Act, 2009" in rep_data["disclaimer"]

    # 3. Retrieve report via GET
    get_rep = client.get(f"/api/inspections/{insp_id}/report")
    assert get_rep.status_code == 200
    assert get_rep.json()["report_number"] == rep_data["report_number"]

    # 4. Download PDF
    pdf_resp = client.get(f"/api/inspections/{insp_id}/report/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000
    assert pdf_resp.content[:4] == b"%PDF"
