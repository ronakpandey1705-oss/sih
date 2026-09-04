import os
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scan import Scan
from app.models.image import UploadedImage
from app.models.ocr_result import OCRResult
from app.models.detected_field import DetectedField
from app.models.complaint import ComplaintReport
from app.schemas.report import (
    DiscrepancyResponse,
    EvidencePackageResponse,
    InspectionReportCreateRequest,
    InspectionReportResponse,
    UnifiedAnalysisResponse
)
from app.services.discrepancy.discrepancy_service import DiscrepancyService
from app.services.evidence.evidence_service import EvidenceService
from app.services.reports.report_service import ReportService
from app.services.extraction.field_extractor import FieldExtractor
from app.services.compliance.rules_engine import RulesEngine
from app.services.ocr.paddle_ocr import PaddleOCRService

router = APIRouter(prefix="/scans/{scan_id}", tags=["Reports & Evidence"])
inspections_reports_router = APIRouter(prefix="/inspections/{scan_id}", tags=["Official Inspection Reports"])


def _verify_scan_exists(scan_id: str, db: Session) -> Scan:
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection/Scan session '{scan_id}' not found"
        )
    return scan


# --- Evidence Collation Endpoint ---
def _handle_get_evidence(scan_id: str, db: Session) -> EvidencePackageResponse:
    _verify_scan_exists(scan_id, db)
    data = EvidenceService.collate_evidence(scan_id, db)
    return EvidencePackageResponse(**data)


@router.get("/evidence", response_model=EvidencePackageResponse, summary="Get collated evidence package")
@inspections_reports_router.get("/evidence", response_model=EvidencePackageResponse, summary="Get official inspection evidence package")
def get_evidence_endpoint(scan_id: str, db: Session = Depends(get_db)):
    """
    Returns complete collated evidence package for frontend canvas rendering:
    packaging photos, OCR bounding box polygons, detected declaration coordinates,
    compliance evaluations, and catalog discrepancy findings.
    """
    return _handle_get_evidence(scan_id, db)


# --- Discrepancy Endpoint ---
def _handle_get_discrepancies(scan_id: str, db: Session) -> DiscrepancyResponse:
    _verify_scan_exists(scan_id, db)
    data = DiscrepancyService.check_discrepancies(scan_id, db)
    return DiscrepancyResponse(**data)


@router.get("/discrepancies", response_model=DiscrepancyResponse, summary="Get catalog vs package discrepancies")
@inspections_reports_router.get("/discrepancies", response_model=DiscrepancyResponse, summary="Get official inspection discrepancies")
def get_discrepancies_endpoint(scan_id: str, db: Session = Depends(get_db)):
    """
    Conservative comparison of registered catalog product data vs observed package declarations.
    Detects net quantity variance, price overcharging, and brand mismatches.
    """
    return _handle_get_discrepancies(scan_id, db)


# --- Inspection Report Generation Endpoints ---
def _handle_generate_report(
    scan_id: str,
    payload: Optional[InspectionReportCreateRequest],
    db: Session
) -> InspectionReportResponse:
    _verify_scan_exists(scan_id, db)

    # Ensure field extraction & compliance evaluation have run before generating report
    if db.query(DetectedField).filter(DetectedField.scan_id == scan_id).count() == 0:
        FieldExtractor.extract_from_scan(scan_id, db)

    RulesEngine.evaluate_scan(scan_id, db)

    notes = payload.officer_notes if payload else None
    auth_name = payload.authority_name if payload else None
    auth_jur = payload.authority_jurisdiction if payload else None

    report = ReportService.generate_inspection_report(
        scan_id=scan_id,
        db=db,
        officer_notes=notes,
        authority_name=auth_name,
        authority_jurisdiction=auth_jur
    )

    full_rep_dict = None
    if report.full_report_json:
        try:
            full_rep_dict = json.loads(report.full_report_json)
        except Exception:
            pass

    return InspectionReportResponse(
        id=report.id,
        scan_id=report.scan_id,
        inspection_id=report.scan_id,
        report_number=report.complaint_number,
        title=report.title,
        summary=report.summary,
        authority_name=report.authority_name,
        authority_jurisdiction=report.authority_jurisdiction,
        status=report.status,
        pdf_path=report.pdf_path,
        pdf_download_url=f"/api/inspections/{scan_id}/report/pdf",
        created_at=report.created_at,
        disclaimer=report.disclaimer,
        full_report=full_rep_dict
    )


@router.post("/report", response_model=InspectionReportResponse, summary="Generate inspection report")
@inspections_reports_router.post("/report", response_model=InspectionReportResponse, summary="Generate official Legal Metrology inspection report & PDF")
def generate_report_endpoint(
    scan_id: str,
    payload: Optional[InspectionReportCreateRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Generates and persists the official Legal Metrology Inspection Notice and Report.
    Constructs downloadable PDF with government layout, findings, and officer determination.
    """
    return _handle_generate_report(scan_id, payload, db)


# --- Get Existing Report ---
def _handle_get_report(scan_id: str, db: Session) -> InspectionReportResponse:
    _verify_scan_exists(scan_id, db)
    report = db.query(ComplaintReport).filter(ComplaintReport.scan_id == scan_id).first()
    if not report:
        # Generate automatically if not yet created
        return _handle_generate_report(scan_id, None, db)

    full_rep_dict = None
    if report.full_report_json:
        try:
            full_rep_dict = json.loads(report.full_report_json)
        except Exception:
            pass

    return InspectionReportResponse(
        id=report.id,
        scan_id=report.scan_id,
        inspection_id=report.scan_id,
        report_number=report.complaint_number,
        title=report.title,
        summary=report.summary,
        authority_name=report.authority_name,
        authority_jurisdiction=report.authority_jurisdiction,
        status=report.status,
        pdf_path=report.pdf_path,
        pdf_download_url=f"/api/inspections/{scan_id}/report/pdf",
        created_at=report.created_at,
        disclaimer=report.disclaimer,
        full_report=full_rep_dict
    )


@router.get("/report", response_model=InspectionReportResponse, summary="Get inspection report record")
@inspections_reports_router.get("/report", response_model=InspectionReportResponse, summary="Get official inspection report record")
def get_report_endpoint(scan_id: str, db: Session = Depends(get_db)):
    """Retrieve the generated inspection report details and summary."""
    return _handle_get_report(scan_id, db)


# --- Download PDF Endpoint ---
def _handle_download_pdf(scan_id: str, db: Session) -> FileResponse:
    _verify_scan_exists(scan_id, db)
    report = db.query(ComplaintReport).filter(ComplaintReport.scan_id == scan_id).first()
    if not report or not report.pdf_path or not os.path.exists(report.pdf_path):
        # Generate report & PDF now
        report = ReportService.generate_inspection_report(scan_id, db)

    if not report.pdf_path or not os.path.exists(report.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF document could not be generated."
        )

    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(report.pdf_path)
    )


@router.get("/report/pdf", summary="Download inspection report PDF")
@inspections_reports_router.get("/report/pdf", summary="Download official Legal Metrology inspection report PDF")
def download_pdf_endpoint(scan_id: str, db: Session = Depends(get_db)):
    """Downloads the official publication-ready PDF document."""
    return _handle_download_pdf(scan_id, db)


# --- Unified One-Shot Analysis Endpoint ---
def _handle_analyze(scan_id: str, db: Session) -> UnifiedAnalysisResponse:
    scan = _verify_scan_exists(scan_id, db)

    # 1. Check if OCR results exist; if images exist without OCR, run PaddleOCR automatically
    existing_ocr_count = db.query(OCRResult).filter(OCRResult.scan_id == scan_id).count()
    if existing_ocr_count == 0:
        images = db.query(UploadedImage).filter(UploadedImage.scan_id == scan_id).all()
        if images:
            ocr_service = PaddleOCRService.get_instance()
            for img in images:
                target_path = img.preprocessed_path if img.preprocessed_path and os.path.exists(img.preprocessed_path) else img.original_path
                if os.path.exists(target_path):
                    ocr_items = ocr_service.process_image(target_path, img.id)
                    PaddleOCRService.save_ocr_results_to_db(db, scan_id, img.id, ocr_items)

    # 2. Extract declarations
    extracted_fields = FieldExtractor.extract_from_scan(scan_id, db)

    # 3. Evaluate compliance
    eval_resp = RulesEngine.evaluate_scan(scan_id, db)

    # 4. Check discrepancies
    disc_data = DiscrepancyService.check_discrepancies(scan_id, db)

    rules_summary_list = [
        {
            "rule_id": r.rule_id,
            "rule_number": r.rule_number,
            "name": r.name,
            "status": r.status,
            "reason": r.reason,
            "severity": r.severity
        }
        for r in eval_resp.results
    ]

    return UnifiedAnalysisResponse(
        inspection_id=scan.id,
        scan_id=scan.id,
        status=eval_resp.status,
        overall_score=eval_resp.overall_score,
        risk_level=eval_resp.risk_level,
        fields_extracted_count=len(extracted_fields),
        rules_evaluated_count=eval_resp.total_rules,
        passed_rules_count=eval_resp.passed_count,
        potential_non_compliance_count=eval_resp.potential_non_compliance_count,
        items_needing_review_count=eval_resp.needs_review_count,
        catalog_discrepancies_count=disc_data.get("total_discrepancies", 0),
        officer_determination=scan.officer_determination,
        summary=f"{eval_resp.summary} {disc_data.get('summary', '')}".strip(),
        discrepancies=disc_data.get("discrepancies", []),
        rules_summary=rules_summary_list
    )


@router.post("/analyze", response_model=UnifiedAnalysisResponse, summary="One-shot packaging compliance screening")
@inspections_reports_router.post("/analyze", response_model=UnifiedAnalysisResponse, summary="One-shot official inspection screening")
def analyze_endpoint(scan_id: str, db: Session = Depends(get_db)):
    """
    Unified one-shot endpoint for frontend convenience:
    Runs OCR (if pending) -> extracts declarations -> evaluates compliance against rules.json
    -> checks catalog discrepancies -> returns unified summary in a single call.
    """
    return _handle_analyze(scan_id, db)
