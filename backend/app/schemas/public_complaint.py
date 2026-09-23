from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

ISSUE_TYPES = {
    "MRP_MISSING": "MRP not printed or unclear",
    "MRP_OVERCHARGED": "Charged above printed MRP",
    "NET_QUANTITY": "Net quantity missing or wrong",
    "MANUFACTURER_DETAILS": "Manufacturer / packer / importer address missing",
    "CONSUMER_CARE": "Consumer care details missing",
    "MFG_DATE": "Manufacturing / import date missing",
    "EXPIRY_DATE": "Best before / expiry date missing",
    "COUNTRY_OF_ORIGIN": "Country of origin missing (imported goods)",
    "ILLEGIBLE_LABEL": "Label unreadable, too small or tampered",
    "MISLEADING_LABEL": "Label is wrong or misleading",
    "OTHER": "Other labelling issue",
}

COMPLAINT_STATUSES = ("NEW", "UNDER_REVIEW", "ACTION_TAKEN", "DISMISSED")


class ComplaintPhotoOut(BaseModel):
    id: str
    url: str


class PublicComplaintCreated(BaseModel):
    reference_no: str
    status: str
    photo_count: int
    message: str


class PublicComplaintTrack(BaseModel):
    reference_no: str
    product_name: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class PublicComplaintOut(BaseModel):
    id: str
    reference_no: str
    product_name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    issue_types: List[str]
    issue_labels: List[str]
    description: str
    store_name: Optional[str] = None
    location: str
    purchase_date: Optional[str] = None
    contact: Optional[str] = None
    status: str
    officer_notes: Optional[str] = None
    handled_by_badge: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    photos: List[ComplaintPhotoOut] = []


class ComplaintSummary(BaseModel):
    total: int
    new_count: int
    latest_reference_no: Optional[str] = None
    latest_created_at: Optional[datetime] = None


class ComplaintUpdate(BaseModel):
    status: Optional[str] = Field(None, description="NEW, UNDER_REVIEW, ACTION_TAKEN or DISMISSED")
    officer_notes: Optional[str] = Field(None, max_length=4000)
