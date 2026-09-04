from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    brand = Column(String(128), nullable=False)
    category = Column(String(128), nullable=True)
    expected_net_quantity = Column(String(64), nullable=False)
    expected_mrp = Column(String(64), nullable=False)
    manufacturer = Column(String(255), nullable=False)
    manufacturer_address = Column(String(512), nullable=False)
    packer = Column(String(255), nullable=True)
    importer = Column(String(255), nullable=True)
    consumer_care_details = Column(String(512), nullable=True)
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to scans
    scans = relationship("Scan", back_populates="product")
