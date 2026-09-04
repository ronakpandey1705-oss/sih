import io
import os
import cv2
import numpy as np
from PIL import Image
from app.services.vision.preprocessing import ImagePreprocessor


def _create_synthetic_packaging_image() -> io.BytesIO:
    # Create image with text contours
    img = np.ones((400, 600, 3), dtype=np.uint8) * 240
    # Draw dark background text
    cv2.putText(img, "LEGAL METROLOGY TEST", (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
    cv2.putText(img, "MRP Rs. 100.00", (40, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
    cv2.putText(img, "NET WEIGHT: 500g", (40, 260), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)

    success, buf = cv2.imencode(".png", img)
    return io.BytesIO(buf.tobytes())


def test_image_preprocessor_pipeline_functions():
    test_img = np.ones((500, 500, 3), dtype=np.uint8) * 200

    # 1. Resize
    resized, scale = ImagePreprocessor.resize_for_ocr(test_img, min_dimension=800)
    assert resized.shape[0] >= 800
    assert scale > 1.0

    # 2. Grayscale
    gray = ImagePreprocessor.to_grayscale(resized)
    assert len(gray.shape) == 2

    # 3. Denoise
    denoised = ImagePreprocessor.denoise(gray)
    assert denoised.shape == gray.shape

    # 4. CLAHE contrast
    enhanced = ImagePreprocessor.enhance_contrast(denoised)
    assert enhanced.shape == gray.shape

    # 5. Skew angle detection
    angle = ImagePreprocessor.detect_skew_angle(enhanced)
    assert isinstance(angle, float)


def test_preprocess_endpoint(client):
    scan_resp = client.post("/api/scans/", json={})
    scan_id = scan_resp.json()["scan_id"]

    img_bytes = _create_synthetic_packaging_image()
    upload_resp = client.post(
        f"/api/scans/{scan_id}/images",
        files={"file": ("pack_label.png", img_bytes, "image/png")}
    )
    image_id = upload_resp.json()["image_id"]

    # Call preprocess endpoint
    prep_resp = client.post(f"/api/scans/{scan_id}/images/{image_id}/preprocess")
    assert prep_resp.status_code == 200
    data = prep_resp.json()
    assert data["image_id"] == image_id
    assert data["clahe_applied"] is True
    assert data["denoised"] is True
    assert os.path.exists(data["preprocessed_path"])
    assert len(data["original_dimensions"]) == 2
    assert len(data["preprocessed_dimensions"]) == 2
