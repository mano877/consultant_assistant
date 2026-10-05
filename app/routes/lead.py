"""Lead endpoints — save qualified leads and list them for demo review."""

import logging
import uuid
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.schemas import LeadCreate, LeadOut
from app.config import LEADS_ADMIN_TOKEN
from app.services.lead_scoring import infer_lead_status
from app.services.intake import split_legacy

logger = logging.getLogger(__name__)
router = APIRouter()
bearer = HTTPBearer(auto_error=False)


def require_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    # Fail closed when the backend secret is not configured.
    if not LEADS_ADMIN_TOKEN or credentials is None or not secrets.compare_digest(
        credentials.credentials.encode(), LEADS_ADMIN_TOKEN.encode()
    ):
        raise HTTPException(
            status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Bearer"}
        )


def _lead_to_out(lead: Lead) -> LeadOut:
    return LeadOut(
        id=str(lead.id),
        session_id=lead.session_id,
        name=lead.name,
        email=lead.email,
        phone_whatsapp=lead.phone_whatsapp,
        course_interest=lead.course_interest,
        preferred_location=lead.preferred_location,
        current_education=lead.current_education,
        english_test_status=lead.english_test_status,
        budget_intake=lead.budget_intake,
        budget=lead.budget,
        intake=lead.intake,
        current_country_status=lead.current_country_status,
        lead_status=lead.lead_status,
        created_at=lead.created_at.isoformat(),
    )


@router.post("/lead", response_model=LeadOut)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    try:
        legacy_budget, legacy_intake = split_legacy(payload.budget_intake)
        budget = payload.budget or legacy_budget
        intake = payload.intake or legacy_intake
        lead = Lead(
            id=uuid.uuid4(),
            session_id=payload.session_id,
            name=payload.name,
            email=payload.email,
            phone_whatsapp=payload.phone_whatsapp,
            course_interest=payload.course_interest,
            preferred_location=payload.preferred_location,
            current_education=payload.current_education,
            english_test_status=payload.english_test_status,
            budget_intake=payload.budget_intake,
            budget=budget,
            intake=intake,
            current_country_status=payload.current_country_status,
            lead_status=infer_lead_status({**payload.model_dump(), "intake": intake}),
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return _lead_to_out(lead)
    except Exception as exc:
        logger.exception("Failed to save lead for session %s", payload.session_id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save lead")


@router.get("/leads", response_model=list[LeadOut], dependencies=[Depends(require_admin)])
def list_leads(db: Session = Depends(get_db)):
    try:
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
        return [_lead_to_out(l) for l in leads]
    except Exception as exc:
        logger.exception("Failed to list leads")
        raise HTTPException(status_code=500, detail="Failed to retrieve leads")
