from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.officer import Officer
from app.schemas.auth import SignupRequest, LoginRequest, AuthResponse
from app.schemas.officer import OfficerProfile
from app.services.auth import hash_password, verify_password, create_token, get_current_officer

router = APIRouter(prefix="/auth", tags=["Officer Authentication"])


def _next_badge(db: Session) -> str:
    """Generate the next free LM-2026-NNN badge number."""
    n = db.query(Officer).count() + 1
    while True:
        badge = f"LM-2026-{n:03d}"
        if not db.query(Officer).filter(Officer.officer_badge == badge).first():
            return badge
        n += 1


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED, summary="Register an officer account")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    if db.query(Officer).filter(func.lower(Officer.email) == req.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists. Please sign in.")

    officer = Officer(
        officer_badge=_next_badge(db),
        name=req.name,
        email=req.email,
        provider="password",
        designation=(req.designation or "").strip() or "Legal Metrology Officer",
        jurisdiction=(req.jurisdiction or "").strip() or "Central Enforcement Directorate",
        phone=(req.phone or "").strip() or None,
        status="ACTIVE",
        password_hash=hash_password(req.password),
    )
    db.add(officer)
    db.commit()
    db.refresh(officer)
    return AuthResponse(
        token=create_token(officer),
        officer=OfficerProfile.model_validate(officer),
        message=f"Registration successful. Welcome {officer.name} ({officer.officer_badge}).",
    )


@router.post("/login", response_model=AuthResponse, summary="Sign in with email and password")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = (req.email or "").strip().lower()
    officer = db.query(Officer).filter(func.lower(Officer.email) == email).first()
    if not officer or not verify_password(req.password or "", officer.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if officer.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is not active")
    return AuthResponse(
        token=create_token(officer),
        officer=OfficerProfile.model_validate(officer),
        message=f"Welcome back {officer.name} ({officer.officer_badge}).",
    )


@router.get("/me", response_model=OfficerProfile, summary="Current signed-in officer")
def me(officer: Officer = Depends(get_current_officer)):
    return OfficerProfile.model_validate(officer)
