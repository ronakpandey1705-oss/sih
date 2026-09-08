import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    officer_badge = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    provider = Column(String(32), default="gmail")  # gmail, yahoo, apple, gov
    designation = Column(String(128), default="Legal Metrology Officer")
    jurisdiction = Column(String(128), default="Central Enforcement Directorate")
    status = Column(String(32), default="ACTIVE")  # ACTIVE, PENDING_VERIFICATION, SUSPENDED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OfficerHelpdeskRequest(Base):
    __tablename__ = "officer_helpdesk_requests"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    ticket_no = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False, index=True)
    provider = Column(String(32), nullable=True)
    claimed_name = Column(String(128), nullable=True)
    status = Column(String(32), default="PENDING_REVIEW")  # PENDING_REVIEW, VERIFIED, REJECTED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
