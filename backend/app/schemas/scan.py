from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.product import ProductResponse


class ScanCreate(BaseModel):
    barcode: Optional[str] = Field(None, examples=["8901234567890"], description="Optional scanned product barcode")
    officer_id: Optional[str] = Field(None, examples=["LM-INSP-2026-441"], description="Legal Metrology Officer/Inspector ID")
    establishment_name: Optional[str] = Field(None, examples=["M/s SuperRetail Mart, Bandra"], description="Inspected shop or commercial establishment name")
    inspection_location: Optional[str] = Field(None, examples=["Bandra West, Mumbai, Maharashtra"], description="Inspection location / premises address")
    user_location: Optional[str] = Field(None, description="Optional location alias")
    notes: Optional[str] = Field(None, description="Officer notes / preliminary observations")


class ScanCreateResponse(BaseModel):
    scan_id: str
    inspection_id: Optional[str] = None
    barcode: Optional[str] = None
    officer_id: Optional[str] = None
    establishment_name: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    inspection_timestamp: Optional[datetime] = None


class ScanDetailResponse(BaseModel):
    id: str
    scan_id: Optional[str] = None
    inspection_id: Optional[str] = None
    barcode: Optional[str] = None
    officer_id: Optional[str] = None
    establishment_name: Optional[str] = None
    inspection_location: Optional[str] = None
    user_location: Optional[str] = None
    product_id: Optional[int] = None
    product: Optional[ProductResponse] = None
    status: str
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    officer_determination: Optional[str] = None
    officer_remarks: Optional[str] = None
    officer_reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    inspection_timestamp: Optional[datetime] = None
    images_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class OfficerReviewRequest(BaseModel):
    officer_determination: str = Field(
        ...,
        examples=["POTENTIAL_NON_COMPLIANCE_CONFIRMED"],
        description="Official determination e.g. COMPLIANT, POTENTIAL_NON_COMPLIANCE_CONFIRMED, FURTHER_INVESTIGATION, DISMISSED"
    )
    officer_remarks: Optional[str] = Field(
        None,
        examples=["Sample seized under Section 15 of Legal Metrology Act, 2009 for missing mandatory declaration."],
        description="Officer remarks, justification, or directives"
    )
    officer_id: Optional[str] = Field(
        None,
        examples=["LM-INSP-2026-441"],
        description="Optional inspector/officer ID confirming determination"
    )


# Official Aliases for Government Officer Workflow
InspectionCreate = ScanCreate
InspectionCreateResponse = ScanCreateResponse
InspectionDetailResponse = ScanDetailResponse
InspectionReviewRequest = OfficerReviewRequest
