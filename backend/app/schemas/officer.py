from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class OfficerVerifyRequest(BaseModel):
    email: str
    provider: Optional[str] = "gmail"
    claimed_name: Optional[str] = None


class OfficerProfile(BaseModel):
    id: int
    officer_badge: str
    name: str
    email: str
    provider: str
    designation: str
    jurisdiction: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class OfficerVerifyResponse(BaseModel):
    verified: bool
    officer: Optional[OfficerProfile] = None
    message: str
    ticket_no: Optional[str] = None


class HelpdeskTicketResponse(BaseModel):
    ticket_no: str
    email: str
    provider: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
