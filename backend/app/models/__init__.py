from app.database import Base
from app.models.product import Product
from app.models.scan import Scan, Inspection
from app.models.image import UploadedImage
from app.models.ocr_result import OCRResult
from app.models.detected_field import DetectedField
from app.models.compliance import ComplianceResult, Violation
from app.models.complaint import ComplaintReport, InspectionReport

__all__ = [
    "Base",
    "Product",
    "Scan",
    "Inspection",
    "UploadedImage",
    "OCRResult",
    "DetectedField",
    "ComplianceResult",
    "Violation",
    "ComplaintReport",
    "InspectionReport",
]
