from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DiscrepancyItem(BaseModel):
    field: str
    status: str = Field(..., examples=["PASS", "POTENTIAL_DISCREPANCY", "NEEDS_REVIEW", "INFO"])
    catalog_value: Optional[str] = None
    detected_value: Optional[str] = None
    difference_summary: str
    severity: str = "LOW"


class DiscrepancyResponse(BaseModel):
    barcode: Optional[str] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    has_catalog_baseline: bool
    total_discrepancies: int
    items_needing_review: int
    discrepancies: List[DiscrepancyItem]
    summary: str


class EvidencePackageResponse(BaseModel):
    inspection_id: str
    scan_id: str
    officer_id: Optional[str] = None
    establishment_name: Optional[str] = None
    inspection_location: Optional[str] = None
    status: str
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    officer_determination: Optional[str] = None
    officer_remarks: Optional[str] = None
    officer_reviewed_at: Optional[str] = None
    product: Optional[Dict[str, Any]] = None
    images_count: int
    images: List[Dict[str, Any]]
    ocr_items_count: int
    ocr_items: List[Dict[str, Any]]
    detected_fields_count: int
    detected_fields: List[Dict[str, Any]]
    compliance_rules_count: int
    compliance_results: List[Dict[str, Any]]
    violations_count: int
    violations: List[Dict[str, Any]]
    discrepancies: Dict[str, Any]


class InspectionReportCreateRequest(BaseModel):
    officer_notes: Optional[str] = Field(None, description="Optional officer notes to incorporate in report")
    authority_name: Optional[str] = Field(None, examples=["Department of Legal Metrology, Maharashtra"], description="Name of controlling authority")
    authority_jurisdiction: Optional[str] = Field(None, examples=["Mumbai Metropolitan Region"], description="Official jurisdiction")


class InspectionReportResponse(BaseModel):
    id: str
    scan_id: str
    inspection_id: str
    report_number: str
    title: str
    summary: str
    authority_name: Optional[str] = None
    authority_jurisdiction: Optional[str] = None
    status: str
    pdf_path: Optional[str] = None
    pdf_download_url: Optional[str] = None
    created_at: datetime
    disclaimer: str
    full_report: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class UnifiedAnalysisResponse(BaseModel):
    inspection_id: str
    scan_id: str
    status: str
    overall_score: float
    risk_level: str
    fields_extracted_count: int
    rules_evaluated_count: int
    passed_rules_count: int
    potential_non_compliance_count: int
    items_needing_review_count: int
    catalog_discrepancies_count: int
    officer_determination: Optional[str] = None
    summary: str
    discrepancies: List[DiscrepancyItem]
    rules_summary: List[Dict[str, Any]]
    detected_declarations: List[Dict[str, Any]] = []
    missing_declarations: List[Dict[str, Any]] = []
