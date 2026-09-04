def test_create_scan_with_known_barcode(client):
    payload = {
        "barcode": "8901234567890",
        "user_location": "Bandra, Mumbai",
        "notes": "Testing biscuit pack"
    }
    response = client.post("/api/scans/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "scan_id" in data
    assert data["barcode"] == "8901234567890"
    assert data["status"] == "CREATED"

    # Now retrieve scan details
    scan_id = data["scan_id"]
    get_resp = client.get(f"/api/scans/{scan_id}")
    assert get_resp.status_code == 200
    scan_data = get_resp.json()
    assert scan_data["id"] == scan_id
    assert scan_data["barcode"] == "8901234567890"
    assert scan_data["user_location"] == "Bandra, Mumbai"
    assert scan_data["product"] is not None
    assert scan_data["product"]["name"] == "DemoBakes Choco Delight Biscuits"


def test_create_scan_with_unknown_barcode(client):
    payload = {
        "barcode": "9998887776665",
        "user_location": "New Delhi"
    }
    response = client.post("/api/scans/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "scan_id" in data
    assert data["barcode"] == "9998887776665"
    assert data["status"] == "CREATED"

    # Verify session persists and product is None
    scan_id = data["scan_id"]
    get_resp = client.get(f"/api/scans/{scan_id}")
    assert get_resp.status_code == 200
    scan_data = get_resp.json()
    assert scan_data["id"] == scan_id
    assert scan_data["product"] is None


def test_create_scan_without_barcode(client):
    payload = {
        "user_location": "Bengaluru"
    }
    response = client.post("/api/scans/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "scan_id" in data
    assert data["barcode"] is None
    assert data["status"] == "CREATED"


def test_get_nonexistent_scan(client):
    response = client.get("/api/scans/non-existent-uuid-1234")
    assert response.status_code == 404


def test_create_inspection_with_officer_details(client):
    """Test official government inspection creation via /api/inspections/."""
    payload = {
        "barcode": "8901234567890",
        "officer_id": "LM-INSP-2026-441",
        "establishment_name": "M/s SuperRetail Mart, Bandra",
        "inspection_location": "Bandra West, Mumbai, Maharashtra",
        "notes": "Routine market surveillance inspection"
    }
    response = client.post("/api/inspections/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "inspection_id" in data
    assert data["inspection_id"] == data["scan_id"]
    assert data["officer_id"] == "LM-INSP-2026-441"
    assert data["establishment_name"] == "M/s SuperRetail Mart, Bandra"
    assert data["status"] == "INSPECTION_CREATED"
    assert data["inspection_timestamp"] is not None

    # Retrieve official inspection details
    insp_id = data["inspection_id"]
    get_resp = client.get(f"/api/inspections/{insp_id}")
    assert get_resp.status_code == 200
    insp_data = get_resp.json()
    assert insp_data["inspection_id"] == insp_id
    assert insp_data["officer_id"] == "LM-INSP-2026-441"
    assert insp_data["establishment_name"] == "M/s SuperRetail Mart, Bandra"
    assert insp_data["inspection_location"] == "Bandra West, Mumbai, Maharashtra"
    assert insp_data["product"] is not None
    assert insp_data["product"]["name"] == "DemoBakes Choco Delight Biscuits"
    assert insp_data["officer_determination"] is None


def test_inspection_officer_review_and_final_determination(client):
    """Test government officer recording review and final determination."""
    # 1. Create inspection
    create_resp = client.post("/api/inspections/", json={
        "barcode": "8901234567890",
        "officer_id": "LM-INSP-2026-441",
        "establishment_name": "Sharma Provision Store, Andheri",
        "inspection_location": "Andheri East, Mumbai"
    })
    assert create_resp.status_code == 201
    insp_id = create_resp.json()["inspection_id"]

    # 2. Officer reviews evidence and submits final determination
    review_payload = {
        "officer_determination": "POTENTIAL_NON_COMPLIANCE_CONFIRMED",
        "officer_remarks": "Notice issued under Section 15 of Legal Metrology Act for missing mandatory declaration.",
        "officer_id": "LM-INSP-2026-441"
    }
    review_resp = client.post(f"/api/inspections/{insp_id}/review", json=review_payload)
    assert review_resp.status_code == 200
    reviewed_data = review_resp.json()
    assert reviewed_data["status"] == "OFFICER_REVIEWED"
    assert reviewed_data["officer_determination"] == "POTENTIAL_NON_COMPLIANCE_CONFIRMED"
    assert "Notice issued under Section 15" in reviewed_data["officer_remarks"]
    assert reviewed_data["officer_reviewed_at"] is not None

    # 3. Verify that GET reflects the recorded determination
    get_resp = client.get(f"/api/inspections/{insp_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "OFFICER_REVIEWED"
    assert get_resp.json()["officer_determination"] == "POTENTIAL_NON_COMPLIANCE_CONFIRMED"


def test_inspection_images_and_ocr_routing(client):
    """Test packaging image upload and OCR listing using /api/inspections/{id}/ endpoints."""
    import io
    from PIL import Image

    # 1. Create inspection
    insp_resp = client.post("/api/inspections/", json={
        "establishment_name": "Metro Cash & Carry",
        "inspection_location": "Borivali, Mumbai"
    })
    assert insp_resp.status_code == 201
    insp_id = insp_resp.json()["inspection_id"]

    # 2. Upload image via /api/inspections/{id}/images
    img_buf = io.BytesIO()
    Image.new("RGB", (200, 200), color=(255, 255, 255)).save(img_buf, format="JPEG")
    img_buf.seek(0)

    upload_resp = client.post(
        f"/api/inspections/{insp_id}/images",
        files={"file": ("sample.jpg", img_buf, "image/jpeg")}
    )
    assert upload_resp.status_code == 201
    assert upload_resp.json()["scan_id"] == insp_id

    # 3. List images via /api/inspections/{id}/images
    list_resp = client.get(f"/api/inspections/{insp_id}/images")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 4. Check OCR results via /api/inspections/{id}/ocr
    ocr_resp = client.get(f"/api/inspections/{insp_id}/ocr")
    assert ocr_resp.status_code == 200
    assert ocr_resp.json()["scan_id"] == insp_id
