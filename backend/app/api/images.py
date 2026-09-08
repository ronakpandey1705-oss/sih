import os
import json
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.scan import Scan
from app.models.image import UploadedImage
from app.models.ocr_result import OCRResult
from app.schemas.image import (
    ImageUploadResponse,
    ImageDetailResponse,
    PreprocessResultResponse
)
from app.schemas.ocr import (
    OCRScanResponse,
    OCRItemResponse
)
from app.services.vision.preprocessing import ImagePreprocessor
from app.services.ocr.paddle_ocr import PaddleOCRService
from app.services.storage.storage_service import StorageService

router = APIRouter(prefix="/scans/{scan_id}", tags=["Images & OCR"])
inspections_images_router = APIRouter(prefix="/inspections/{scan_id}", tags=["Inspection Images & OCR"])

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/pjpeg": ".jpg",
    "image/jfif": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max


def _verify_scan_exists(scan_id: str, db: Session) -> Scan:
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan session '{scan_id}' not found"
        )
    return scan


@router.post("/images", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED, summary="Upload a packaging image")
@inspections_images_router.post("/images", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED, summary="Upload packaging inspection image")
async def upload_image(
    scan_id: str,
    file: UploadFile = File(..., description="Package photograph (JPG, PNG, or WebP)"),
    user_location: Optional[str] = Form(None, description="Optional user location coordinates or address"),
    db: Session = Depends(get_db)
):
    """
    Upload a package photo associated with a scan session.
    - Validates file type (JPG, PNG, WebP)
    - Normalizes mobile camera orientation (EXIF transpose)
    - Constrains massive mobile resolutions to max 1600px for lightning-fast, low-memory OCR
    - Saves image securely and creates database record
    """
    scan = _verify_scan_exists(scan_id, db)

    # Validate MIME type
    content_type = file.content_type.lower() if file.content_type else ""
    if content_type not in ALLOWED_MIME_TYPES:
        # Fallback check file extension
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{content_type}'. Allowed types: JPG, PNG, WebP"
            )
        matched_ext = ext
    else:
        matched_ext = ALLOWED_MIME_TYPES[content_type]

    # Generate IDs and paths
    image_id = str(uuid.uuid4())
    scan_dir = os.path.join(settings.UPLOAD_DIR, scan_id)
    os.makedirs(scan_dir, exist_ok=True)

    safe_filename = f"{image_id}{matched_ext}"
    dest_path = os.path.join(scan_dir, safe_filename)

    # Save original image
    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image file: {str(e)}"
        )
    finally:
        file.file.close()

    # Mobile camera normalization: correct EXIF orientation (portrait) and optimize resolution
    try:
        from PIL import Image, ImageOps
        with Image.open(dest_path) as pil_img:
            transposed = ImageOps.exif_transpose(pil_img)
            if transposed is not None:
                if transposed.mode not in ("RGB", "L"):
                    transposed = transposed.convert("RGB")
                w, h = transposed.size
                max_side = max(w, h)
                # Rescale high-megapixel phone photos (> 1600px) to prevent 512MB RAM spikes on Render
                if max_side > 1600:
                    scale = 1600.0 / max_side
                    transposed = transposed.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
                transposed.save(dest_path, format="JPEG", quality=90, optimize=True)
    except Exception as norm_err:
        print(f"[IMAGE UPLOAD] Mobile normalization notice: {norm_err}")

    file_size = os.path.getsize(dest_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        try:
            os.remove(dest_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum permitted limit (25 MB)"
        )

    # Create image record in database
    uploaded_image = UploadedImage(
        id=image_id,
        scan_id=scan_id,
        filename=file.filename or safe_filename,
        original_path=dest_path,
        file_size=file_size,
        mime_type=content_type or f"image/{matched_ext.strip('.')}"
    )
    db.add(uploaded_image)

    # Automatic background barcode detection if image contains a 1D or 2D barcode
    detected_barcode = None
    barcode_detected = False
    try:
        from app.services.vision.barcode_service import BarcodeService
        from app.models.product import Product

        b_res = BarcodeService.detect_barcode(dest_path)
        if b_res.get("found") and b_res.get("barcode"):
            detected_barcode = b_res["barcode"]
            barcode_detected = True
            if not scan.barcode:
                scan.barcode = detected_barcode
                matched_product = db.query(Product).filter(Product.barcode == detected_barcode).first()
                if matched_product and not scan.product_id:
                    scan.product_id = matched_product.id
    except Exception as e:
        print(f"[BARCODE_DETECTION] Non-blocking notice: {e}")

    # Optional upload to cloud storage for permanent backup
    try:
        if StorageService.is_cloud_enabled():
            cloud_url = StorageService.upload_image(dest_path, public_id=f"{scan_id}_{image_id}")
            # If upload succeeded, retain local dest_path so OCR/OpenCV have instant zero-latency file access
            if not os.path.exists(dest_path) and cloud_url and cloud_url.startswith("http"):
                uploaded_image.original_path = cloud_url
    except Exception as e:
        print(f"[STORAGE WARNING] Cloud upload notice: {e}")

    # Update scan status and optional location
    scan.status = "IMAGES_UPLOADED"
    if user_location and not scan.user_location:
        scan.user_location = user_location

    db.commit()
    db.refresh(uploaded_image)

    return ImageUploadResponse(
        image_id=uploaded_image.id,
        scan_id=uploaded_image.scan_id,
        filename=uploaded_image.filename,
        file_size=uploaded_image.file_size,
        mime_type=uploaded_image.mime_type,
        created_at=uploaded_image.created_at,
        preprocessed=False,
        barcode_detected=barcode_detected,
        detected_barcode=detected_barcode
    )


@router.get("/images", response_model=List[ImageDetailResponse], summary="List uploaded images for scan session")
@inspections_images_router.get("/images", response_model=List[ImageDetailResponse], summary="List uploaded images for inspection")
def list_scan_images(
    scan_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve all packaging images uploaded for this scan session."""
    _verify_scan_exists(scan_id, db)
    images = db.query(UploadedImage).filter(UploadedImage.scan_id == scan_id).all()
    return [ImageDetailResponse.model_validate(img) for img in images]


@router.get("/images/{image_id}/file", summary="Retrieve uploaded image file or redirect to cloud storage")
@inspections_images_router.get("/images/{image_id}/file", summary="Retrieve uploaded image file or redirect to cloud storage")
def get_image_file(scan_id: str, image_id: str, db: Session = Depends(get_db)):
    """Serve uploaded packaging image from disk or redirect to permanent cloud storage."""
    _verify_scan_exists(scan_id, db)
    image = db.query(UploadedImage).filter(
        UploadedImage.id == image_id,
        UploadedImage.scan_id == scan_id
    ).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Image '{image_id}' not found")
    if image.original_path.startswith("http://") or image.original_path.startswith("https://"):
        return RedirectResponse(image.original_path)
    if os.path.exists(image.original_path):
        return FileResponse(image.original_path, media_type=image.mime_type or "image/jpeg")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found on disk")


@router.post("/images/{image_id}/preprocess", response_model=PreprocessResultResponse, summary="Run OpenCV image preprocessing")
@inspections_images_router.post("/images/{image_id}/preprocess", response_model=PreprocessResultResponse, summary="Run OpenCV image preprocessing for inspection")
def preprocess_image(
    scan_id: str,
    image_id: str,
    deskew: bool = True,
    db: Session = Depends(get_db)
):
    """
    Run OpenCV enhancement on the uploaded packaging image:
    - Normalizes size for OCR
    - Denoises packaging texture while keeping font edges sharp
    - CLAHE contrast enhancement for harsh flash/glare
    - Deskewing text orientation
    Original image remains untouched as evidence.
    """
    _verify_scan_exists(scan_id, db)
    image = db.query(UploadedImage).filter(
        UploadedImage.id == image_id,
        UploadedImage.scan_id == scan_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID '{image_id}' not found in scan session"
        )

    scan_dir = os.path.join(settings.UPLOAD_DIR, scan_id)
    out_path = os.path.join(scan_dir, f"{image_id}_preprocessed.png")

    source_path = StorageService.resolve_local_image_path(image.original_path, scan_id=scan_id)
    if not source_path or not os.path.exists(source_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not accessible on server or storage cache"
        )

    try:
        metrics = ImagePreprocessor.process_pipeline(
            image_path=source_path,
            output_path=out_path,
            deskew=deskew
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image preprocessing failed: {str(e)}"
        )

    image.preprocessed_path = metrics["preprocessed_path"]
    db.commit()

    return PreprocessResultResponse(
        image_id=image_id,
        scan_id=scan_id,
        preprocessed_path=metrics["preprocessed_path"],
        original_dimensions=metrics["original_dimensions"],
        preprocessed_dimensions=metrics["preprocessed_dimensions"],
        skew_angle_detected=metrics["skew_angle_detected"],
        clahe_applied=metrics["clahe_applied"],
        denoised=metrics["denoised"]
    )


@router.post("/images/{image_id}/ocr", response_model=List[OCRItemResponse], summary="Run PaddleOCR on single image")
@inspections_images_router.post("/images/{image_id}/ocr", response_model=List[OCRItemResponse], summary="Run PaddleOCR on inspection image")
def run_ocr_on_image(
    scan_id: str,
    image_id: str,
    use_preprocessed: bool = False,
    db: Session = Depends(get_db)
):
    """
    Run PaddleOCR on the uploaded/preprocessed packaging image.
    Extracts text, recognition confidence, and exact bounding box coordinates.
    Saves results to the database for frontend highlight overlays.
    """
    _verify_scan_exists(scan_id, db)
    image = db.query(UploadedImage).filter(
        UploadedImage.id == image_id,
        UploadedImage.scan_id == scan_id
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with ID '{image_id}' not found"
        )

    # Determine image path (preprocessed if available and requested, else original)
    resolved_original = StorageService.resolve_local_image_path(image.original_path, scan_id=scan_id)
    target_path = resolved_original

    if use_preprocessed and image.preprocessed_path and os.path.exists(image.preprocessed_path):
        target_path = image.preprocessed_path
    elif use_preprocessed and not image.preprocessed_path and target_path:
        scan_dir = os.path.join(settings.UPLOAD_DIR, scan_id)
        out_path = os.path.join(scan_dir, f"{image_id}_preprocessed.png")
        try:
            metrics = ImagePreprocessor.process_pipeline(target_path, out_path)
            image.preprocessed_path = metrics["preprocessed_path"]
            db.commit()
            target_path = image.preprocessed_path
        except Exception:
            target_path = resolved_original

    ocr_service = PaddleOCRService.get_instance()
    extracted_items = ocr_service.process_image(target_path, image_id) if target_path else []

    # Clear previous OCR results for this image if re-running
    db.query(OCRResult).filter(OCRResult.image_id == image_id).delete()
    db.commit()

    # Save new OCR results
    saved_records = ocr_service.save_ocr_results_to_db(db, scan_id, image_id, extracted_items)

    response_items = []
    for r in saved_records:
        parsed_bbox = [0, 0, 0, 0]
        parsed_poly = None
        if r.bbox_json:
            try:
                bdata = json.loads(r.bbox_json)
                parsed_bbox = bdata.get("bbox", [0, 0, 0, 0])
                parsed_poly = bdata.get("polygon")
            except Exception:
                pass

        response_items.append(
            OCRItemResponse(
                id=r.id,
                image_id=r.image_id,
                text=r.text,
                confidence=r.confidence,
                bbox=parsed_bbox,
                polygon=parsed_poly,
                line_order=r.line_order
            )
        )

    return response_items


@router.get("/ocr", response_model=OCRScanResponse, summary="Get all OCR results and bounding boxes for scan session")
@inspections_images_router.get("/ocr", response_model=OCRScanResponse, summary="Get all OCR results and bounding boxes for inspection session")
def get_scan_ocr_results(
    scan_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve all detected OCR lines and bounding boxes for the scan session.
    The frontend uses this to draw overlay boxes on top of packaging photos.
    """
    _verify_scan_exists(scan_id, db)
    results = db.query(OCRResult).filter(OCRResult.scan_id == scan_id).order_by(OCRResult.line_order).all()

    items = []
    total_conf = 0.0
    for r in results:
        parsed_bbox = [0, 0, 0, 0]
        parsed_poly = None
        if r.bbox_json:
            try:
                bdata = json.loads(r.bbox_json)
                parsed_bbox = bdata.get("bbox", [0, 0, 0, 0])
                parsed_poly = bdata.get("polygon")
            except Exception:
                pass

        items.append(
            OCRItemResponse(
                id=r.id,
                image_id=r.image_id,
                text=r.text,
                confidence=r.confidence,
                bbox=parsed_bbox,
                polygon=parsed_poly,
                line_order=r.line_order
            )
        )
        total_conf += r.confidence

    avg_conf = round(total_conf / len(items), 4) if items else 0.0

    return OCRScanResponse(
        scan_id=scan_id,
        total_lines=len(items),
        average_confidence=avg_conf,
        items=items
    )
