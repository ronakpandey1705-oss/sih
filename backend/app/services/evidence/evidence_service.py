import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.models.image import UploadedImage
from app.models.ocr_result import OCRResult
from app.models.detected_field import DetectedField
from app.models.compliance import ComplianceResult, Violation
from app.services.discrepancy.discrepancy_service import DiscrepancyService


class EvidenceService:
    """
    Evidence Collation Service for Legal Metrology Officers.
    Aggregates packaging photos, OCR bounding box polygons, detected declaration coordinates,
    compliance evaluations, and discrepancy findings into a cohesive payload for frontend canvas rendering.
    """

    @classmethod
    def collate_evidence(cls, scan_id: str, db: Session) -> Dict[str, Any]:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise ValueError(f"Inspection session '{scan_id}' not found")

        # 1. Images
        images_db = db.query(UploadedImage).filter(UploadedImage.scan_id == scan_id).all()
        images_list = []
        for img in images_db:
            images_list.append({
                "id": img.id,
                "filename": img.filename,
                "file_size": img.file_size,
                "mime_type": img.mime_type,
                "preprocessed": bool(img.preprocessed_path),
                "created_at": img.created_at.isoformat() if img.created_at else None
            })

        # 2. OCR Items & Polygons
        ocr_db = db.query(OCRResult).filter(OCRResult.scan_id == scan_id).order_by(OCRResult.line_order).all()
        ocr_items = []
        for r in ocr_db:
            parsed_bbox = [0, 0, 0, 0]
            parsed_poly = None
            if r.bbox_json:
                try:
                    bdata = json.loads(r.bbox_json)
                    parsed_bbox = bdata.get("bbox", [0, 0, 0, 0])
                    parsed_poly = bdata.get("polygon")
                except Exception:
                    pass
            ocr_items.append({
                "id": r.id,
                "image_id": r.image_id,
                "text": r.text,
                "confidence": r.confidence,
                "bbox": parsed_bbox,
                "polygon": parsed_poly,
                "line_order": r.line_order
            })

        # 3. Detected Fields
        fields_db = db.query(DetectedField).filter(DetectedField.scan_id == scan_id).all()
        fields_list = []
        for f in fields_db:
            parsed_bbox = None
            if f.bbox_json:
                try:
                    bdata = json.loads(f.bbox_json)
                    parsed_bbox = bdata.get("bbox", bdata if isinstance(bdata, list) else None)
                except Exception:
                    pass
            fields_list.append({
                "id": f.id,
                "field_name": f.field_name,
                "value": f.value,
                "raw_text": f.raw_text,
                "confidence": f.confidence,
                "extraction_method": f.extraction_method,
                "image_id": f.image_id,
                "bbox": parsed_bbox
            })

        # 4. Compliance Results
        comp_db = db.query(ComplianceResult).filter(ComplianceResult.scan_id == scan_id).all()
        comp_items = []
        for cr in comp_db:
            comp_items.append({
                "rule_id": cr.rule_id,
                "field": cr.field,
                "rule_description": cr.rule_description,
                "status": cr.status,
                "confidence": cr.confidence,
                "reason": cr.reason,
                "legal_reference": cr.legal_reference,
                "severity": cr.severity,
                "evidence_text": cr.evidence_text,
                "evidence_image_id": cr.evidence_image_id
            })

        # 5. Violations
        viol_db = db.query(Violation).filter(Violation.scan_id == scan_id).all()
        viol_items = []
        for v in viol_db:
            viol_items.append({
                "id": v.id,
                "rule_id": v.rule_id,
                "title": v.title,
                "description": v.description,
                "severity": v.severity,
                "field": v.field,
                "legal_reference": v.legal_reference
            })

        # 6. Discrepancies
        discrepancy_data = DiscrepancyService.check_discrepancies(scan_id, db)

        return {
            "inspection_id": scan.id,
            "scan_id": scan.id,
            "officer_id": scan.officer_id,
            "establishment_name": scan.establishment_name,
            "inspection_location": scan.inspection_location or scan.user_location,
            "status": scan.status,
            "overall_score": scan.overall_score,
            "risk_level": scan.risk_level,
            "officer_determination": scan.officer_determination,
            "officer_remarks": scan.officer_remarks,
            "officer_reviewed_at": scan.officer_reviewed_at.isoformat() if scan.officer_reviewed_at else None,
            "product": {
                "id": scan.product.id,
                "barcode": scan.product.barcode,
                "name": scan.product.name,
                "brand": scan.product.brand,
                "category": scan.product.category,
                "expected_net_quantity": scan.product.expected_net_quantity,
                "declared_net_quantity": scan.product.expected_net_quantity,
                "expected_mrp": scan.product.expected_mrp
            } if scan.product else None,
            "images_count": len(images_list),
            "images": images_list,
            "ocr_items_count": len(ocr_items),
            "ocr_items": ocr_items,
            "detected_fields_count": len(fields_list),
            "detected_fields": fields_list,
            "compliance_rules_count": len(comp_items),
            "compliance_results": comp_items,
            "violations_count": len(viol_items),
            "violations": viol_items,
            "discrepancies": discrepancy_data
        }
