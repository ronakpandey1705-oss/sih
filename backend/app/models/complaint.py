import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ComplaintReport(Base):
    __tablename__ = "complaint_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    scan_id = Column(String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    complaint_number = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    authority_name = Column(String(255), nullable=True)
    authority_jurisdiction = Column(String(255), nullable=True)
    full_report_json = Column(Text, nullable=False)
    pdf_path = Column(String(512), nullable=True)
    user_location = Column(String(255), nullable=True)
    status = Column(String(32), default="DRAFT", nullable=False)  # DRAFT, GENERATED
    disclaimer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    scan = relationship("Scan", back_populates="complaints")


# Official Alias for Government Officer Inspection Report
InspectionReport = ComplaintReport
