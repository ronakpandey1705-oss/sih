import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    barcode = Column(String(64), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(32), default="CREATED", nullable=False)
    overall_score = Column(Float, nullable=True)
    risk_level = Column(String(32), nullable=True)
    user_location = Column(String(255), nullable=True)
    officer_id = Column(String(64), nullable=True, index=True)  # Legal Metrology Officer/Inspector ID
    establishment_name = Column(String(255), nullable=True)     # Shop / Commercial Establishment Name
    inspection_location = Column(String(255), nullable=True)    # Official premises / location
    notes = Column(Text, nullable=True)

    # Official review & final determination by the Government Officer
    officer_determination = Column(String(64), nullable=True)   # e.g., COMPLIANT, POTENTIAL_NON_COMPLIANCE_CONFIRMED, FURTHER_INVESTIGATION, DISMISSED
    officer_remarks = Column(Text, nullable=True)               # Officer's official written assessment / directives
    officer_reviewed_at = Column(DateTime, nullable=True)       # Timestamp when officer recorded final determination

    # Relationships
    product = relationship("Product", back_populates="scans")
    images = relationship("UploadedImage", back_populates="scan", cascade="all, delete-orphan")
    ocr_results = relationship("OCRResult", back_populates="scan", cascade="all, delete-orphan")
    detected_fields = relationship("DetectedField", back_populates="scan", cascade="all, delete-orphan")
    compliance_results = relationship("ComplianceResult", back_populates="scan", cascade="all, delete-orphan")
    complaints = relationship("ComplaintReport", back_populates="scan", cascade="all, delete-orphan")


# Alias for Government Officer Inspection terminology
Inspection = Scan
