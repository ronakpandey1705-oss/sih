import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class DetectedField(Base):
    __tablename__ = "detected_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    scan_id = Column(String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    image_id = Column(String(36), ForeignKey("uploaded_images.id", ondelete="SET NULL"), nullable=True)
    field_name = Column(String(64), nullable=False, index=True)  # e.g. mrp, net_quantity, manufacturer, etc.
    value = Column(Text, nullable=False)
    raw_text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    extraction_method = Column(String(32), default="REGEX")  # REGEX, KEYWORD, GEMINI
    bbox_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    scan = relationship("Scan", back_populates="detected_fields")
    image = relationship("UploadedImage", back_populates="detected_fields")
