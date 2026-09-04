import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.scan import Scan
from app.models.complaint import ComplaintReport
from app.models.compliance import ComplianceResult
from app.services.evidence.evidence_service import EvidenceService
from app.services.discrepancy.discrepancy_service import DiscrepancyService

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


class ReportService:
    """
    Legal Metrology Inspection Report & PDF Generation Service.
    Constructs official government inspection reports with AI screening findings,
    catalog discrepancies, and human officer final determinations.
    """

    STATUTORY_DISCLAIMER = (
        "STATUTORY NOTICE & LEGAL METROLOGY ACT, 2009 DISCLAIMER:\n"
        "This inspection report was prepared with the assistance of automated computer vision "
        "and compliance screening algorithms. In accordance with statutory principles, the AI system "
        "only identifies potential non-compliances and matters requiring verification. It does not make "
        "legally binding determinations of guilt. Official legal notices, compounding of offences, or seizure "
        "proceedings are executed exclusively under the authority of the designated Legal Metrology Officer "
        "pursuant to the Legal Metrology Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011."
    )

    @classmethod
    def generate_inspection_report(
        cls,
        scan_id: str,
        db: Session,
        officer_notes: Optional[str] = None,
        authority_name: Optional[str] = None,
        authority_jurisdiction: Optional[str] = None
    ) -> ComplaintReport:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise ValueError(f"Inspection session '{scan_id}' not found")

        # 1. Collate evidence & discrepancies
        evidence = EvidenceService.collate_evidence(scan_id, db)
        discrepancy_data = evidence.get("discrepancies", {})

        # 2. Formulate report number & title
        now_utc = datetime.now(timezone.utc)
        date_str = now_utc.strftime("%Y%m%d")
        unique_suffix = str(uuid.uuid4())[:6].upper()
        report_num = f"LM-INSP-{date_str}-{unique_suffix}"
        title = f"Official Inspection Report - {scan.establishment_name or 'Commercial Establishment'}"

        # 3. Compile full JSON payload
        full_payload = {
            "report_number": report_num,
            "generated_at": now_utc.isoformat(),
            "inspection_session": {
                "id": scan.id,
                "officer_id": scan.officer_id,
                "establishment_name": scan.establishment_name,
                "inspection_location": scan.inspection_location or scan.user_location,
                "status": scan.status,
                "overall_score": scan.overall_score,
                "risk_level": scan.risk_level,
                "officer_determination": scan.officer_determination,
                "officer_remarks": scan.officer_remarks or officer_notes,
                "officer_reviewed_at": scan.officer_reviewed_at.isoformat() if scan.officer_reviewed_at else None
            },
            "product_information": evidence.get("product"),
            "compliance_findings": {
                "overall_score": scan.overall_score,
                "risk_level": scan.risk_level,
                "rules": evidence.get("compliance_results", [])
            },
            "discrepancy_findings": discrepancy_data,
            "violations": evidence.get("violations", []),
            "detected_declarations": evidence.get("detected_fields", []),
            "disclaimer": cls.STATUTORY_DISCLAIMER
        }

        # 4. Generate PDF file
        scan_dir = os.path.join(settings.UPLOAD_DIR, scan_id)
        os.makedirs(scan_dir, exist_ok=True)
        pdf_filename = f"inspection_report_{report_num}.pdf"
        pdf_path = os.path.join(scan_dir, pdf_filename)

        cls._create_pdf(pdf_path, full_payload)

        # 5. Persist record in database (complaint_reports table)
        summary_text = (
            f"Official inspection conducted at {scan.establishment_name or 'premises'} by Officer {scan.officer_id or 'N/A'}. "
            f"AI screening score: {scan.overall_score or 0.0}% ({scan.risk_level or 'PENDING'} risk). "
            f"Officer Determination: {scan.officer_determination or 'PENDING_OFFICER_REVIEW'}."
        )

        existing_report = db.query(ComplaintReport).filter(ComplaintReport.scan_id == scan_id).first()
        if existing_report:
            report = existing_report
            report.complaint_number = report_num
            report.title = title
            report.summary = summary_text
            report.full_report_json = json.dumps(full_payload)
            report.pdf_path = pdf_path
            report.authority_name = authority_name or "Legal Metrology Department"
            report.authority_jurisdiction = authority_jurisdiction or scan.inspection_location or "General Jurisdiction"
            report.status = "GENERATED"
            report.disclaimer = cls.STATUTORY_DISCLAIMER
        else:
            report = ComplaintReport(
                scan_id=scan_id,
                complaint_number=report_num,
                title=title,
                summary=summary_text,
                authority_name=authority_name or "Legal Metrology Department",
                authority_jurisdiction=authority_jurisdiction or scan.inspection_location or "General Jurisdiction",
                full_report_json=json.dumps(full_payload),
                pdf_path=pdf_path,
                user_location=scan.inspection_location or scan.user_location,
                status="GENERATED",
                disclaimer=cls.STATUTORY_DISCLAIMER
            )
            db.add(report)

        db.commit()
        db.refresh(report)
        return report

    @classmethod
    def _create_pdf(cls, output_path: str, data: Dict[str, Any]):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1e3a8a"),
            alignment=1,  # Center
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#475569"),
            alignment=1,
            spaceAfter=12
        )

        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#1e293b")
        )

        small_style = ParagraphStyle(
            "SmallBody",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b")
        )

        elements = []

        # Header
        elements.append(Paragraph("GOVERNMENT OF INDIA / STATE LEGAL METROLOGY", title_style))
        elements.append(Paragraph(
            "OFFICIAL INSPECTION REPORT & SCREENING NOTICE<br/>"
            "Under The Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011",
            subtitle_style
        ))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=10))

        # Section 1: Inspection Identification
        insp = data.get("inspection_session", {})
        info_data = [
            [
                Paragraph(f"<b>Report No:</b> {data.get('report_number')}", body_style),
                Paragraph(f"<b>Inspection Date:</b> {data.get('generated_at', '')[:10]}", body_style)
            ],
            [
                Paragraph(f"<b>Officer ID:</b> {insp.get('officer_id') or 'N/A'}", body_style),
                Paragraph(f"<b>Establishment:</b> {insp.get('establishment_name') or 'N/A'}", body_style)
            ],
            [
                Paragraph(f"<b>Location:</b> {insp.get('inspection_location') or 'Not Specified'}", body_style),
                Paragraph(f"<b>Status:</b> {insp.get('status')}", body_style)
            ]
        ]
        info_table = Table(info_data, colWidths=[270, 270])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10))

        # Section 2: Commodity & Barcode Identification
        prod = data.get("product_information") or {}
        cat_mrp = str(prod.get('expected_mrp', 'N/A'))
        if cat_mrp != 'N/A' and not cat_mrp.startswith('₹'):
            cat_mrp = f"₹{cat_mrp}"
        net_qty_display = prod.get('expected_net_quantity') or prod.get('declared_net_quantity') or 'N/A'
        elements.append(Paragraph("1. PACKAGED COMMODITY IDENTIFICATION", heading_style))
        prod_data = [
            [
                Paragraph(f"<b>Barcode (EAN/UPC):</b> {prod.get('barcode') or 'Unscanned / Unknown'}", body_style),
                Paragraph(f"<b>Commodity Name:</b> {prod.get('name') or 'N/A'}", body_style)
            ],
            [
                Paragraph(f"<b>Category:</b> {prod.get('category') or 'N/A'}", body_style),
                Paragraph(f"<b>Registered Net Qty:</b> {net_qty_display}", body_style)
            ],
            [
                Paragraph(f"<b>Expected Catalog MRP:</b> {cat_mrp}", body_style),
                Paragraph(f"<b>Brand:</b> {prod.get('brand') or 'N/A'}", body_style)
            ]
        ]
        prod_table = Table(prod_data, colWidths=[270, 270])
        prod_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(prod_table)
        elements.append(Spacer(1, 10))

        # Section 3: AI Compliance Screening Matrix
        elements.append(Paragraph("2. LEGAL METROLOGY COMPLIANCE SCREENING MATRIX (RULES LM-01 TO LM-10)", heading_style))
        score_val = insp.get("overall_score", 0.0)
        risk_val = insp.get("risk_level", "PENDING")
        elements.append(Paragraph(
            f"<b>Overall AI Screening Score:</b> {score_val}% &nbsp;|&nbsp; <b>Risk Assessment:</b> {risk_val}",
            body_style
        ))
        elements.append(Spacer(1, 4))

        rules_list = data.get("compliance_findings", {}).get("rules", [])
        rules_table_data = [
            [
                Paragraph("<b>Rule</b>", body_style),
                Paragraph("<b>Requirement</b>", body_style),
                Paragraph("<b>Status</b>", body_style),
                Paragraph("<b>Finding / Evidence</b>", body_style)
            ]
        ]

        for r in rules_list:
            st = r.get("status", "")
            if st == "PASS":
                color_hex = "#166534"
            elif st == "POTENTIAL_NON_COMPLIANCE":
                color_hex = "#991b1b"
            elif st == "NEEDS_REVIEW":
                color_hex = "#854d0e"
            else:
                color_hex = "#475569"

            rules_table_data.append([
                Paragraph(f"<b>{r.get('rule_id')}</b>", body_style),
                Paragraph(r.get("rule_description", ""), body_style),
                Paragraph(f"<font color='{color_hex}'><b>{st}</b></font>", body_style),
                Paragraph(r.get("reason") or r.get("evidence_text") or "-", body_style)
            ])

        rules_table = Table(rules_table_data, colWidths=[55, 145, 120, 220])
        rules_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(rules_table)
        elements.append(Spacer(1, 10))

        # Section 4: Discrepancy Findings
        disc_items = data.get("discrepancy_findings", {}).get("discrepancies", [])
        if disc_items:
            elements.append(Paragraph("3. CATALOG VS PACKAGING DISCREPANCY FINDINGS", heading_style))
            disc_table_data = [
                [
                    Paragraph("<b>Field</b>", body_style),
                    Paragraph("<b>Status</b>", body_style),
                    Paragraph("<b>Catalog Spec</b>", body_style),
                    Paragraph("<b>Observed Package Declaration</b>", body_style)
                ]
            ]
            for d in disc_items:
                disc_table_data.append([
                    Paragraph(d.get("field", ""), body_style),
                    Paragraph(f"<b>{d.get('status')}</b>", body_style),
                    Paragraph(str(d.get("catalog_value") or "-"), body_style),
                    Paragraph(d.get("difference_summary", ""), body_style)
                ])
            disc_table = Table(disc_table_data, colWidths=[90, 100, 110, 240])
            disc_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(disc_table)
            elements.append(Spacer(1, 10))

        # Section 5: Officer Final Determination & Remarks
        elements.append(Paragraph("4. INSPECTING OFFICER OFFICIAL DETERMINATION", heading_style))
        determination_val = insp.get("officer_determination") or "PENDING OFFICIAL OFFICER DETERMINATION"
        remarks_val = insp.get("officer_remarks") or "No additional written directives recorded at time of report generation."

        det_data = [
            [Paragraph(f"<b>Official Legal Determination:</b> <font color='#1e3a8a'><b>{determination_val}</b></font>", body_style)],
            [Paragraph(f"<b>Officer Written Directives / Seizure Orders:</b><br/>{remarks_val}", body_style)],
            [Paragraph(f"<b>Officer Review Stamped At:</b> {insp.get('officer_reviewed_at') or 'Pending Review'}", body_style)]
        ]
        det_table = Table(det_data, colWidths=[540])
        det_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(det_table)
        elements.append(Spacer(1, 10))

        # Section 6: Statutory Disclaimer & Signature Block
        elements.append(Paragraph(data.get("disclaimer", ""), small_style))
        elements.append(Spacer(1, 15))

        sig_data = [
            [
                Paragraph("<b>Inspected Establishment Signature / Seal:</b><br/><br/><br/>____________________________________", body_style),
                Paragraph("<b>Inspecting Legal Metrology Officer:</b><br/><br/><br/>____________________________________<br/>Name & Official Seal", body_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[270, 270])
        sig_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(sig_table)

        doc.build(elements)
