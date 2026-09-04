import io
import cv2
import numpy as np


def _create_ocr_test_packaging_image() -> io.BytesIO:
    img = np.ones((350, 700, 3), dtype=np.uint8) * 255
    # High-contrast clear packaging declaration text
    cv2.putText(img, "MRP Rs. 50.00", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 2)
    cv2.putText(img, "Net Qty: 200 g", (50, 170), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 2)
    cv2.putText(img, "Mfd: 06/2026", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 2)

    success, buf = cv2.imencode(".png", img)
    return io.BytesIO(buf.tobytes())


def test_ocr_endpoint_and_bounding_boxes(client):
    scan_resp = client.post("/api/scans/", json={"barcode": "8901234567890"})
    scan_id = scan_resp.json()["scan_id"]

    img_bytes = _create_ocr_test_packaging_image()
    upload_resp = client.post(
        f"/api/scans/{scan_id}/images",
        files={"file": ("label_declarations.png", img_bytes, "image/png")}
    )
    image_id = upload_resp.json()["image_id"]

    # Run OCR endpoint on this image
    ocr_resp = client.post(f"/api/scans/{scan_id}/images/{image_id}/ocr")
    assert ocr_resp.status_code == 200
    lines = ocr_resp.json()
    assert isinstance(lines, list)
    assert len(lines) >= 2

    # Check text, confidence, and bounding box structure
    texts = [item["text"] for item in lines]
    all_text = " ".join(texts)
    assert "MRP" in all_text or "50" in all_text
    assert "200" in all_text or "Qty" in all_text

    first_item = lines[0]
    assert "text" in first_item
    assert "confidence" in first_item
    assert first_item["confidence"] > 0.5
    assert "bbox" in first_item
    assert len(first_item["bbox"]) == 4
    assert first_item["image_id"] == image_id

    # Now verify GET /api/scans/{scan_id}/ocr endpoint
    scan_ocr_resp = client.get(f"/api/scans/{scan_id}/ocr")
    assert scan_ocr_resp.status_code == 200
    scan_ocr_data = scan_ocr_resp.json()
    assert scan_ocr_data["scan_id"] == scan_id
    assert scan_ocr_data["total_lines"] == len(lines)
    assert scan_ocr_data["average_confidence"] > 0.5
    assert len(scan_ocr_data["items"]) == len(lines)
