import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    scan_id = Column(String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False)
    field = Column(String(64), nullable=False)
    rule_description = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False)  # PASS, POTENTIAL_VIOLATION, NEEDS_REVIEW, NOT_APPLICABLE
    confidence = Column(Float, nullable=False, default=1.0)
    reason = Column(Text, nullable=True)
    legal_reference = Column(String(255), nullable=True)
    severity = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    evidence_text = Column(Text, nullable=True)
    evidence_image_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    scan = relationship("Scan", back_populates="compliance_results")


class Violation(Base):
    __tablename__ = "violations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    scan_id = Column(String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(32), default="MEDIUM")
    field = Column(String(64), nullable=False)
    evidence_json = Column(Text, nullable=True)  # Store JSON with image_id, bbox, text, confidence
    legal_reference = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
