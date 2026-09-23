from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.officer import OfficerProfile


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    designation: Optional[str] = Field(None, max_length=128)
    jurisdiction: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=32)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    officer: OfficerProfile
    message: str
