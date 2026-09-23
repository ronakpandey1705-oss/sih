import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class PublicComplaint(Base):
    """Anonymous citizen complaint about a packaged product's label."""
    __tablename__ = "public_complaints"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    reference_no = Column(String(32), unique=True, index=True, nullable=False)
    product_name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=True)
    barcode = Column(String(64), nullable=True)
    issue_types = Column(Text, nullable=False)  # JSON list of issue codes
    description = Column(Text, nullable=False)
    store_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=False)
    purchase_date = Column(String(32), nullable=True)
    contact = Column(String(255), nullable=True)  # Optional; citizen may stay anonymous
    status = Column(String(32), default="NEW", nullable=False)  # NEW, UNDER_REVIEW, ACTION_TAKEN, DISMISSED
    officer_notes = Column(Text, nullable=True)
    handled_by_badge = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    photos = relationship(
        "PublicComplaintPhoto",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="PublicComplaintPhoto.position",
    )


class PublicComplaintPhoto(Base):
    __tablename__ = "public_complaint_photos"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    complaint_id = Column(String(36), ForeignKey("public_complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, default=0)
    path = Column(String(1024), nullable=False)  # Local path or cloud URL
    mime_type = Column(String(64), default="image/jpeg")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    complaint = relationship("PublicComplaint", back_populates="photos")
