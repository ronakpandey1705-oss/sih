import random
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.officer import Officer, OfficerHelpdeskRequest
from app.schemas.officer import (
    OfficerVerifyRequest,
    OfficerVerifyResponse,
    OfficerProfile,
    HelpdeskTicketResponse,
)

router = APIRouter(prefix="/officers", tags=["Officer Verification"])


@router.post("/verify", response_model=OfficerVerifyResponse, summary="Verify officer credentials")
def verify_officer(req: OfficerVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifies whether an email belongs to an authorized Legal Metrology Officer.
    If not recognized, creates an official helpdesk referral ticket.
    """
    clean_email = (req.email or "").strip().lower()
    if not clean_email:
        raise HTTPException(status_code=400, detail="Email address is required")

    officer = (
        db.query(Officer)
        .filter(func.lower(Officer.email) == clean_email, Officer.status == "ACTIVE")
        .first()
    )

    if officer:
        return OfficerVerifyResponse(
            verified=True,
            officer=OfficerProfile.model_validate(officer),
            message=f"Official credentials verified. Welcome {officer.name} ({officer.officer_badge})."
        )

    # Unknown credential: generate official helpdesk referral ticket
    ticket_num = f"LM-HLP-{random.randint(100000, 999999)}"
    ticket = OfficerHelpdeskRequest(
        ticket_no=ticket_num,
        email=clean_email,
        provider=req.provider or "unknown",
        claimed_name=req.claimed_name,
        status="PENDING_REVIEW",
        notes="Automatic referral: Unregistered credentials attempted portal access."
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return OfficerVerifyResponse(
        verified=False,
        officer=None,
        ticket_no=ticket_num,
        message=(
            f"The identity '{clean_email}' is not listed in the National Legal Metrology Officer Database. "
            f"Statutory inspection access is restricted exclusively to authorized government enforcement officers. "
            f"Verification ticket {ticket_num} has been created and forwarded to the Central Helpdesk for manual credential validation."
        )
    )


@router.get("/demo", response_model=List[OfficerProfile], summary="List registered reference officers")
def get_demo_officers(db: Session = Depends(get_db)):
    """Returns registered authorized officers for quick testing."""
    officers = db.query(Officer).filter(Officer.status == "ACTIVE").all()
    return [OfficerProfile.model_validate(o) for o in officers]


@router.get("/tickets", response_model=List[HelpdeskTicketResponse], summary="List pending helpdesk verification tickets")
def get_helpdesk_tickets(db: Session = Depends(get_db)):
    """Returns recently created officer helpdesk verification requests."""
    tickets = db.query(OfficerHelpdeskRequest).order_by(OfficerHelpdeskRequest.created_at.desc()).limit(20).all()
    return [HelpdeskTicketResponse.model_validate(t) for t in tickets]
