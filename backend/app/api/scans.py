from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scan import Scan
from app.models.product import Product
from app.schemas.scan import (
    ScanCreate,
    ScanCreateResponse,
    ScanDetailResponse,
    OfficerReviewRequest,
    InspectionCreate,
    InspectionCreateResponse,
    InspectionDetailResponse,
    InspectionReviewRequest,
)
from app.schemas.product import ProductResponse

# Primary router for scans (backward compatible)
router = APIRouter(prefix="/scans", tags=["Inspections & Scans"])

# Dedicated router with official Government Officer Inspection prefix
inspections_router = APIRouter(prefix="/inspections", tags=["Inspections & Scans"])


def _handle_create_inspection(payload: ScanCreate, db: Session) -> ScanCreateResponse:
    clean_barcode = payload.barcode.strip() if payload.barcode else None
    product_id = None

    if clean_barcode:
        product = db.query(Product).filter(Product.barcode == clean_barcode).first()
        if product:
            product_id = product.id

    # Support both inspection_location and user_location smoothly
    location = payload.inspection_location or payload.user_location

    scan = Scan(
        barcode=clean_barcode,
        product_id=product_id,
        officer_id=payload.officer_id,
        establishment_name=payload.establishment_name,
        inspection_location=location,
        user_location=location,
        notes=payload.notes,
        status="INSPECTION_CREATED" if (payload.officer_id or payload.establishment_name) else "CREATED"
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    return ScanCreateResponse(
        scan_id=scan.id,
        inspection_id=scan.id,
        barcode=scan.barcode,
        officer_id=scan.officer_id,
        establishment_name=scan.establishment_name,
        status=scan.status,
        created_at=scan.created_at,
        inspection_timestamp=scan.created_at
    )


def _handle_get_inspection(scan_id: str, db: Session) -> ScanDetailResponse:
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection/Scan session with ID '{scan_id}' not found"
        )

    product_resp = None
    if scan.product:
        product_resp = ProductResponse.model_validate(scan.product)

    location = scan.inspection_location or scan.user_location

    return ScanDetailResponse(
        id=scan.id,
        inspection_id=scan.id,
        scan_id=scan.id,
        barcode=scan.barcode,
        officer_id=scan.officer_id,
        establishment_name=scan.establishment_name,
        inspection_location=location,
        user_location=location,
        product_id=scan.product_id,
        product=product_resp,
        status=scan.status,
        overall_score=scan.overall_score,
        risk_level=scan.risk_level,
        officer_determination=scan.officer_determination,
        officer_remarks=scan.officer_remarks,
        officer_reviewed_at=scan.officer_reviewed_at,
        notes=scan.notes,
        created_at=scan.created_at,
        inspection_timestamp=scan.created_at,
        images_count=len(scan.images) if scan.images else 0
    )


def _handle_review_inspection(scan_id: str, payload: OfficerReviewRequest, db: Session) -> ScanDetailResponse:
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection session with ID '{scan_id}' not found"
        )

    scan.officer_determination = payload.officer_determination
    if payload.officer_remarks:
        scan.officer_remarks = payload.officer_remarks
    if payload.officer_id:
        scan.officer_id = payload.officer_id

    scan.officer_reviewed_at = datetime.now(timezone.utc)
    scan.status = "OFFICER_REVIEWED"

    db.commit()
    db.refresh(scan)
    return _handle_get_inspection(scan.id, db)


# --- /api/scans endpoints ---
@router.post("/", response_model=ScanCreateResponse, status_code=status.HTTP_201_CREATED, summary="Create a new inspection/scan session")
def create_scan(payload: ScanCreate, db: Session = Depends(get_db)):
    """Initiate a new inspection/scan session."""
    return _handle_create_inspection(payload, db)


@router.get("/{scan_id}", response_model=ScanDetailResponse, summary="Get inspection/scan session details")
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """Retrieve details and status for an inspection/scan session."""
    return _handle_get_inspection(scan_id, db)


@router.post("/{scan_id}/review", response_model=ScanDetailResponse, summary="Submit officer review / determination")
def review_scan(scan_id: str, payload: OfficerReviewRequest, db: Session = Depends(get_db)):
    """Record officer review and determination."""
    return _handle_review_inspection(scan_id, payload, db)


# --- /api/inspections endpoints (Official Officer terminology) ---
@inspections_router.post("/", response_model=InspectionCreateResponse, status_code=status.HTTP_201_CREATED, summary="Create a government officer inspection")
def create_inspection(payload: InspectionCreate, db: Session = Depends(get_db)):
    """
    Initiate an official Legal Metrology inspection session.
    Accepts officer ID, establishment/shop name, optional location, and barcode.
    """
    return _handle_create_inspection(payload, db)


@inspections_router.get("/{inspection_id}", response_model=InspectionDetailResponse, summary="Get official inspection details")
def get_inspection(inspection_id: str, db: Session = Depends(get_db)):
    """Retrieve complete official inspection record by inspection ID."""
    return _handle_get_inspection(inspection_id, db)


@inspections_router.post("/{inspection_id}/review", response_model=InspectionDetailResponse, summary="Record officer review and final determination")
def review_inspection(inspection_id: str, payload: InspectionReviewRequest, db: Session = Depends(get_db)):
    """
    Record officer review and final determination.
    The AI only flags Potential Non-Compliance; the authorized government officer
    records the final determination (e.g. COMPLIANT, POTENTIAL_NON_COMPLIANCE_CONFIRMED,
    FURTHER_INVESTIGATION, DISMISSED) and written remarks.
    """
    return _handle_review_inspection(inspection_id, payload, db)
