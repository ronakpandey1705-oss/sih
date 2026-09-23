"""Password hashing and signed officer session tokens (stdlib only)."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.officer import Officer

_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: Optional[str]) -> bool:
    if not stored:
        return False
    try:
        _, iterations, salt, expected = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations))
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(payload: str) -> str:
    return _b64(hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest())


def create_token(officer: Officer) -> str:
    body = {"sub": officer.id, "exp": int(time.time()) + settings.SESSION_TTL_HOURS * 3600}
    payload = _b64(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    return f"{payload}.{_sign(payload)}"


def decode_token(token: str) -> Optional[int]:
    """Return the officer id for a valid, unexpired token, else None."""
    try:
        payload, signature = token.split(".")
        if not hmac.compare_digest(signature, _sign(payload)):
            return None
        body = json.loads(_unb64(payload))
        if int(body["exp"]) < time.time():
            return None
        return int(body["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def get_current_officer(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Officer:
    """FastAPI dependency: require a valid `Authorization: Bearer <token>` header."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Officer sign-in required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthorized
    officer_id = decode_token(authorization.split(" ", 1)[1].strip())
    if officer_id is None:
        raise unauthorized
    officer = db.query(Officer).filter(Officer.id == officer_id, Officer.status == "ACTIVE").first()
    if not officer:
        raise unauthorized
    return officer
