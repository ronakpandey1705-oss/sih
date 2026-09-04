import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scan import Scan
from app.models.detected_field import DetectedField
from app.models.compliance import ComplianceResult
from app.schemas.compliance import (
    DetectedFieldItem,
    ExtractedFieldsResponse,
    RuleEvaluationItem,
    ComplianceEvaluationResponse,
    RuleDefinitionItem,
    RulesetConfigResponse
)
from app.services.extraction.field_extractor import FieldExtractor
from app.services.compliance.rules_engine import RulesEngine

router = APIRouter(prefix="/scans/{scan_id}", tags=["Compliance & Rules Engine"])
inspections_compliance_router = APIRouter(prefix="/inspections/{scan_id}", tags=["Official Inspection Compliance"])
public_compliance_router = APIRouter(prefix="/compliance", tags=["Legal Metrology Ruleset"])


def _verify_scan_exists(scan_id: str, db: Session) -> Scan:
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection/Scan session '{scan_id}' not found"
        )
    return scan


# --- Ruleset Configuration Endpoint ---
@public_compliance_router.get("/rules", response_model=RulesetConfigResponse, summary="Get active Legal Metrology ruleset configuration")
def get_ruleset_configuration():
    """
    Returns the active Legal Metrology (Packaged Commodities) ruleset configuration
    loaded directly from rules/rules.json. Frontend uses this to render compliance criteria.
    """
    config = RulesEngine.load_rules()
    rule_items = [
        RuleDefinitionItem(
            id=r["id"],
            rule_number=r["rule_number"],
            name=r["name"],
            field=r["field"],
            mandatory=r.get("mandatory", True),
            description=r["description"],
            severity=r.get("severity", "MEDIUM"),
            legal_reference=r.get("legal_reference", "")
        )
        for r in config.get("rules", [])
    ]
    return RulesetConfigResponse(
        metadata=config.get("metadata", {}),
        total_rules=len(rule_items),
        rules=rule_items,
        schedules=config.get("schedules", {}),
        exemptions=config.get("exemptions", {}),
        amendments=config.get("amendments", [])
    )


# --- Field Extraction Handlers ---
def _handle_extract_fields(scan_id: str, db: Session) -> ExtractedFieldsResponse:
    _verify_scan_exists(scan_id, db)
    saved_fields = FieldExtractor.extract_from_scan(scan_id, db)

    items = []
    for f in saved_fields:
        parsed_bbox = None
        if f.bbox_json:
            try:
                bdata = json.loads(f.bbox_json)
                parsed_bbox = bdata.get("bbox", bdata if isinstance(bdata, list) else None)
            except Exception:
                pass

        items.append(
            DetectedFieldItem(
                id=f.id,
                field_name=f.field_name,
                value=f.value,
                raw_text=f.raw_text,
                confidence=f.confidence,
                extraction_method=f.extraction_method,
                image_id=f.image_id,
                bbox=parsed_bbox,
                created_at=f.created_at
            )
        )

    return ExtractedFieldsResponse(
        scan_id=scan_id,
        inspection_id=scan_id,
        total_fields=len(items),
        fields=items
    )


@router.post("/extract-fields", response_model=ExtractedFieldsResponse, summary="Extract declarations from OCR results")
@inspections_compliance_router.post("/extract-fields", response_model=ExtractedFieldsResponse, summary="Extract declarations for inspection")
def extract_fields_endpoint(scan_id: str, db: Session = Depends(get_db)):
    """
    NLP and Heuristic mapping of packaging OCR text into structured Legal Metrology
    declarations: product name, net quantity, MRP, unit sale price, manufacturer,
    consumer care, date, and dimensions.
    """
    return _handle_extract_fields(scan_id, db)


# --- Compliance Evaluation Handlers ---
def _handle_evaluate_compliance(scan_id: str, db: Session) -> ComplianceEvaluationResponse:
    _verify_scan_exists(scan_id, db)

    # Ensure field extraction has been executed
    existing_fields = db.query(DetectedField).filter(DetectedField.scan_id == scan_id).count()
    if existing_fields == 0:
        FieldExtractor.extract_from_scan(scan_id, db)

    return RulesEngine.evaluate_scan(scan_id, db)


@router.post("/evaluate", response_model=ComplianceEvaluationResponse, summary="Evaluate compliance against Legal Metrology rules")
@inspections_compliance_router.post("/evaluate", response_model=ComplianceEvaluationResponse, summary="Run compliance screening on inspection")
def evaluate_compliance_endpoint(scan_id: str, db: Session = Depends(get_db)):
    """
    Evaluate detected declarations against the configured ruleset (rules/rules.json).
    Checks Rules LM-01 to LM-10, small-package exemptions under Rule 26, font size (Rule 7),
    placement (Rule 8), and legibility (Rule 9).
    Returns PASS, POTENTIAL_NON_COMPLIANCE, NEEDS_REVIEW, or NOT_APPLICABLE.
    """
    return _handle_evaluate_compliance(scan_id, db)


# --- Retrieve Existing Compliance Results ---
def _handle_get_compliance(scan_id: str, db: Session) -> ComplianceEvaluationResponse:
    scan = _verify_scan_exists(scan_id, db)

    results = (
        db.query(ComplianceResult)
        .filter(ComplianceResult.scan_id == scan_id)
        .all()
    )

    if not results:
        # Evaluate automatically if not yet evaluated
        return _handle_evaluate_compliance(scan_id, db)

    items = []
    for r in results:
        items.append(
            RuleEvaluationItem(
                rule_id=r.rule_id,
                rule_number=r.rule_description.split(":")[0].strip() if ":" in r.rule_description else r.rule_id,
                name=r.rule_description.split(":")[1].strip() if ":" in r.rule_description else r.rule_id,
                field=r.field,
                status=r.status,
                confidence=r.confidence,
                severity=r.severity,
                reason=r.reason,
                legal_reference=r.legal_reference,
                evidence_text=r.evidence_text,
                evidence_image_id=r.evidence_image_id
            )
        )

    passed_count = sum(1 for i in items if i.status == "PASS")
    pnc_count = sum(1 for i in items if i.status == "POTENTIAL_NON_COMPLIANCE")
    needs_review_count = sum(1 for i in items if i.status == "NEEDS_REVIEW")
    na_count = sum(1 for i in items if i.status == "NOT_APPLICABLE")

    summary_text = (
        f"AI screening score: {scan.overall_score or 0.0}% ({scan.risk_level or 'PENDING'} risk). "
        f"{pnc_count} potential non-compliances, {needs_review_count} items requiring review."
    )

    return ComplianceEvaluationResponse(
        scan_id=scan.id,
        inspection_id=scan.id,
        status=scan.status,
        overall_score=scan.overall_score or 0.0,
        risk_level=scan.risk_level or "PENDING",
        total_rules=len(items),
        passed_count=passed_count,
        potential_non_compliance_count=pnc_count,
        needs_review_count=needs_review_count,
        not_applicable_count=na_count,
        officer_determination=scan.officer_determination,
        officer_remarks=scan.officer_remarks,
        officer_reviewed_at=scan.officer_reviewed_at,
        summary=summary_text,
        results=items
    )


@router.get("/compliance", response_model=ComplianceEvaluationResponse, summary="Get scan compliance results")
@inspections_compliance_router.get("/compliance", response_model=ComplianceEvaluationResponse, summary="Get official inspection compliance results")
def get_compliance_results_endpoint(scan_id: str, db: Session = Depends(get_db)):
    """Retrieve the compliance evaluation results for an inspection session."""
    return _handle_get_compliance(scan_id, db)
