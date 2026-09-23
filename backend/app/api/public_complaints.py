import os
import json
import uuid
import secrets
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.officer import Officer
from app.models.public_complaint import PublicComplaint, PublicComplaintPhoto
from app.schemas.public_complaint import (
    ISSUE_TYPES,
    COMPLAINT_STATUSES,
    ComplaintPhotoOut,
    PublicComplaintCreated,
    PublicComplaintTrack,
    PublicComplaintOut,
    ComplaintSummary,
    ComplaintUpdate,
)
from app.services.auth import get_current_officer
from app.services.storage.storage_service import StorageService

router = APIRouter(prefix="/public-complaints", tags=["Public Complaints"])

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/pjpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_PHOTOS = 6
MAX_PHOTO_BYTES = 15 * 1024 * 1024


def _clean(value: Optional[str], limit: int) -> Optional[str]:
    value = (value or "").strip()
    return value[:limit] if value else None


def _new_reference(db: Session) -> str:
    stamp = datetime.now(timezone.utc).strftime("%y%m")
    while True:
        ref = f"PC-{stamp}-{secrets.token_hex(3).upper()}"
        if not db.query(PublicComplaint).filter(PublicComplaint.reference_no == ref).first():
            return ref


def _save_photo(upload: UploadFile, complaint_id: str) -> tuple[str, str]:
    """Validate, normalise (EXIF rotate + downscale) and store one photo. Returns (path, mime)."""
    content_type = (upload.content_type or "").lower()
    ext = os.path.splitext(upload.filename or "")[1].lower()
    if content_type not in ALLOWED_MIME_TYPES and ext not in (".jpg", ".jpeg", ".png", ".webp"):
        raise HTTPException(status_code=400, detail=f"'{upload.filename}' is not a supported image (use JPG, PNG or WebP)")

    raw = upload.file.read(MAX_PHOTO_BYTES + 1)
    upload.file.close()
    if len(raw) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail=f"'{upload.filename}' is larger than 15 MB")
    if not raw:
        raise HTTPException(status_code=400, detail=f"'{upload.filename}' is empty")

    folder = os.path.join(settings.UPLOAD_DIR, "public_complaints", complaint_id)
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, f"{uuid.uuid4()}.jpg")

    try:
        import io
        from PIL import Image, ImageOps
        with Image.open(io.BytesIO(raw)) as img:
            img = ImageOps.exif_transpose(img) or img
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            w, h = img.size
            if max(w, h) > 1800:
                scale = 1800.0 / max(w, h)
                img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            img.save(dest, format="JPEG", quality=88, optimize=True)
    except Exception:
        raise HTTPException(status_code=400, detail=f"'{upload.filename}' could not be read as an image")

    stored = StorageService.upload_image(dest, folder="packsure/public_complaints")
    return stored, "image/jpeg"


def _to_out(c: PublicComplaint) -> PublicComplaintOut:
    try:
        codes = json.loads(c.issue_types or "[]")
    except json.JSONDecodeError:
        codes = []
    photos = [
        ComplaintPhotoOut(
            id=p.id,
            url=p.path if p.path.startswith(("http://", "https://"))
            else f"/api/public-complaints/{c.id}/photos/{p.id}",
        )
        for p in c.photos
    ]
    return PublicComplaintOut(
        id=c.id,
        reference_no=c.reference_no,
        product_name=c.product_name,
        brand=c.brand,
        barcode=c.barcode,
        issue_types=codes,
        issue_labels=[ISSUE_TYPES.get(code, code) for code in codes],
        description=c.description,
        store_name=c.store_name,
        location=c.location,
        purchase_date=c.purchase_date,
        contact=c.contact,
        status=c.status,
        officer_notes=c.officer_notes,
        handled_by_badge=c.handled_by_badge,
        created_at=c.created_at,
        updated_at=c.updated_at,
        photos=photos,
    )


# ---------------------------------------------------------------------------
# Public (no sign-in) endpoints
# ---------------------------------------------------------------------------

@router.get("/issue-types", summary="List reportable labelling issues")
def list_issue_types():
    return [{"code": k, "label": v} for k, v in ISSUE_TYPES.items()]


@router.post("", response_model=PublicComplaintCreated, status_code=status.HTTP_201_CREATED, summary="File an anonymous product label complaint")
def create_complaint(
    product_name: str = Form(..., description="Product name as printed on the pack"),
    issue_types: List[str] = Form(..., description="One or more issue codes"),
    description: str = Form(..., description="What is wrong with the label"),
    location: str = Form(..., description="City / district / state where the product was found"),
    brand: Optional[str] = Form(None),
    barcode: Optional[str] = Form(None),
    store_name: Optional[str] = Form(None),
    purchase_date: Optional[str] = Form(None),
    contact: Optional[str] = Form(None, description="Optional phone or email for follow-up"),
    photos: List[UploadFile] = File(default=[], description="Up to 6 photos of the product label"),
    db: Session = Depends(get_db),
):
    product_name = _clean(product_name, 255)
    description = _clean(description, 4000)
    location = _clean(location, 255)
    if not product_name or not description or not location:
        raise HTTPException(status_code=422, detail="Product name, description and location are required")

    # Browsers may send a single comma-joined value or repeated fields
    codes: List[str] = []
    for raw in issue_types:
        for code in (raw or "").split(","):
            code = code.strip().upper()
            if code and code not in codes:
                codes.append(code)
    unknown = [c for c in codes if c not in ISSUE_TYPES]
    if not codes or unknown:
        raise HTTPException(status_code=422, detail="Select at least one valid issue type")

    photos = [p for p in (photos or []) if p is not None and (p.filename or "")]
    if len(photos) > MAX_PHOTOS:
        raise HTTPException(status_code=400, detail=f"You can attach at most {MAX_PHOTOS} photos")

    complaint = PublicComplaint(
        reference_no=_new_reference(db),
        product_name=product_name,
        brand=_clean(brand, 255),
        barcode=_clean(barcode, 64),
        issue_types=json.dumps(codes),
        description=description,
        store_name=_clean(store_name, 255),
        location=location,
        purchase_date=_clean(purchase_date, 32),
        contact=_clean(contact, 255),
        status="NEW",
    )
    db.add(complaint)
    db.flush()

    for idx, upload in enumerate(photos):
        path, mime = _save_photo(upload, complaint.id)
        db.add(PublicComplaintPhoto(complaint_id=complaint.id, position=idx, path=path, mime_type=mime))

    db.commit()
    return PublicComplaintCreated(
        reference_no=complaint.reference_no,
        status=complaint.status,
        photo_count=len(photos),
        message="Your complaint has been registered and forwarded to Legal Metrology officers.",
    )


@router.get("/track/{reference_no}", response_model=PublicComplaintTrack, summary="Check complaint status by reference number")
def track_complaint(reference_no: str, db: Session = Depends(get_db)):
    c = db.query(PublicComplaint).filter(PublicComplaint.reference_no == reference_no.strip().upper()).first()
    if not c:
        raise HTTPException(status_code=404, detail="No complaint found with this reference number")
    return PublicComplaintTrack(
        reference_no=c.reference_no,
        product_name=c.product_name,
        status=c.status,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


# ---------------------------------------------------------------------------
# Officer-only endpoints
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=ComplaintSummary, summary="Unread complaint counter for officer notifications")
def complaint_summary(db: Session = Depends(get_db), officer: Officer = Depends(get_current_officer)):
    latest = db.query(PublicComplaint).order_by(PublicComplaint.created_at.desc()).first()
    return ComplaintSummary(
        total=db.query(PublicComplaint).count(),
        new_count=db.query(PublicComplaint).filter(PublicComplaint.status == "NEW").count(),
        latest_reference_no=latest.reference_no if latest else None,
        latest_created_at=latest.created_at if latest else None,
    )


@router.get("", response_model=List[PublicComplaintOut], summary="List citizen complaints")
def list_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    q = db.query(PublicComplaint)
    if status_filter and status_filter.upper() != "ALL":
        q = q.filter(PublicComplaint.status == status_filter.upper())
    return [_to_out(c) for c in q.order_by(PublicComplaint.created_at.desc()).limit(limit).all()]


def _get_or_404(complaint_id: str, db: Session) -> PublicComplaint:
    c = db.query(PublicComplaint).filter(PublicComplaint.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return c


@router.get("/{complaint_id}", response_model=PublicComplaintOut, summary="Get one citizen complaint")
def get_complaint(complaint_id: str, db: Session = Depends(get_db), officer: Officer = Depends(get_current_officer)):
    return _to_out(_get_or_404(complaint_id, db))


@router.patch("/{complaint_id}", response_model=PublicComplaintOut, summary="Update complaint status / officer notes")
def update_complaint(
    complaint_id: str,
    req: ComplaintUpdate,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    c = _get_or_404(complaint_id, db)
    if req.status is not None:
        new_status = req.status.upper()
        if new_status not in COMPLAINT_STATUSES:
            raise HTTPException(status_code=422, detail=f"Status must be one of {', '.join(COMPLAINT_STATUSES)}")
        c.status = new_status
    if req.officer_notes is not None:
        c.officer_notes = req.officer_notes.strip() or None
    c.handled_by_badge = officer.officer_badge
    c.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(c)
    return _to_out(c)


@router.get("/{complaint_id}/photos/{photo_id}", summary="Serve a complaint photo")
def get_complaint_photo(
    complaint_id: str,
    photo_id: str,
    db: Session = Depends(get_db),
    officer: Officer = Depends(get_current_officer),
):
    photo = db.query(PublicComplaintPhoto).filter(
        PublicComplaintPhoto.id == photo_id,
        PublicComplaintPhoto.complaint_id == complaint_id,
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    if photo.path.startswith(("http://", "https://")):
        return RedirectResponse(photo.path)
    if os.path.exists(photo.path):
        return FileResponse(photo.path, media_type=photo.mime_type or "image/jpeg")
    raise HTTPException(status_code=404, detail="Photo file not found on disk")
