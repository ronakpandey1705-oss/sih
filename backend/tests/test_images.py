import io
import pytest
from PIL import Image


def _create_dummy_image(format="JPEG") -> io.BytesIO:
    file = io.BytesIO()
    image = Image.new("RGB", (300, 200), color=(240, 240, 240))
    image.save(file, format=format)
    file.seek(0)
    return file


def test_upload_image_success(client):
    # Create scan first
    scan_resp = client.post("/api/scans/", json={"barcode": "8901234567890"})
    assert scan_resp.status_code == 201
    scan_id = scan_resp.json()["scan_id"]

    # Upload image
    img_bytes = _create_dummy_image("JPEG")
    response = client.post(
        f"/api/scans/{scan_id}/images",
        files={"file": ("label.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 201
    data = response.json()
    assert "image_id" in data
    assert data["scan_id"] == scan_id
    assert data["filename"] == "label.jpg"
    assert data["file_size"] > 0
    assert data["preprocessed"] is False

    # Check that scan status was updated to IMAGES_UPLOADED
    scan_detail = client.get(f"/api/scans/{scan_id}").json()
    assert scan_detail["status"] == "IMAGES_UPLOADED"
    assert scan_detail["images_count"] == 1


def test_upload_image_with_optional_location(client):
    scan_resp = client.post("/api/scans/", json={})
    scan_id = scan_resp.json()["scan_id"]

    img_bytes = _create_dummy_image("PNG")
    response = client.post(
        f"/api/scans/{scan_id}/images",
        files={"file": ("packaging.png", img_bytes, "image/png")},
        data={"user_location": "Bandra West, Mumbai"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "image_id" in data

    # Verify scan has updated user_location
    scan_detail = client.get(f"/api/scans/{scan_id}").json()
    assert scan_detail["user_location"] == "Bandra West, Mumbai"


def test_upload_image_unsupported_type(client):
    scan_resp = client.post("/api/scans/", json={})
    scan_id = scan_resp.json()["scan_id"]

    fake_text_file = io.BytesIO(b"Not an image")
    response = client.post(
        f"/api/scans/{scan_id}/images",
        files={"file": ("test.txt", fake_text_file, "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_image_to_nonexistent_scan(client):
    img_bytes = _create_dummy_image("JPEG")
    response = client.post(
        "/api/scans/invalid-scan-uuid/images",
        files={"file": ("label.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 404


def test_list_scan_images(client):
    scan_resp = client.post("/api/scans/", json={})
    scan_id = scan_resp.json()["scan_id"]

    # Upload two images
    img1 = _create_dummy_image("JPEG")
    img2 = _create_dummy_image("PNG")
    client.post(f"/api/scans/{scan_id}/images", files={"file": ("f1.jpg", img1, "image/jpeg")})
    client.post(f"/api/scans/{scan_id}/images", files={"file": ("f2.png", img2, "image/png")})

    response = client.get(f"/api/scans/{scan_id}/images")
    assert response.status_code == 200
    images = response.json()
    assert len(images) == 2
    filenames = [img["filename"] for img in images]
    assert "f1.jpg" in filenames
    assert "f2.png" in filenames
