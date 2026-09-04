from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DetectedFieldItem(BaseModel):
    id: Optional[str] = None
    field_name: str
    value: str
    raw_text: Optional[str] = None
    confidence: float = 1.0
    extraction_method: str = "REGEX_HEURISTICS"
    image_id: Optional[str] = None
    bbox: Optional[List[int]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractedFieldsResponse(BaseModel):
    scan_id: str
    inspection_id: Optional[str] = None
    total_fields: int
    fields: List[DetectedFieldItem]


class RuleEvaluationItem(BaseModel):
    rule_id: str = Field(..., examples=["LM-01"])
    rule_number: str = Field(..., examples=["Rule 6(1)(b)"])
    name: str = Field(..., examples=["Product Name and Identity"])
    field: str = Field(..., examples=["product_name"])
    status: str = Field(..., examples=["PASS", "POTENTIAL_NON_COMPLIANCE", "NEEDS_REVIEW", "NOT_APPLICABLE"])
    confidence: float = 1.0
    severity: str = "MEDIUM"
    reason: Optional[str] = None
    legal_reference: Optional[str] = None
    evidence_text: Optional[str] = None
    evidence_image_id: Optional[str] = None


class ComplianceEvaluationResponse(BaseModel):
    scan_id: str
    inspection_id: Optional[str] = None
    status: str
    overall_score: float
    risk_level: str
    total_rules: int
    passed_count: int
    potential_non_compliance_count: int
    needs_review_count: int
    not_applicable_count: int
    officer_determination: Optional[str] = None
    officer_remarks: Optional[str] = None
    officer_reviewed_at: Optional[datetime] = None
    summary: str
    results: List[RuleEvaluationItem]


class RuleDefinitionItem(BaseModel):
    id: str
    rule_number: str
    name: str
    field: str
    mandatory: bool
    description: str
    severity: str
    legal_reference: str


class RulesetConfigResponse(BaseModel):
    metadata: Dict[str, Any]
    total_rules: int
    rules: List[RuleDefinitionItem]
    schedules: Dict[str, Any]
    exemptions: Dict[str, Any]
    amendments: List[Dict[str, Any]]
