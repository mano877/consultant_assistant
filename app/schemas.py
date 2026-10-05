import re
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

SessionId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")]
RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
LeadStatus = Literal["LOW_INTENT", "MEDIUM_INTENT", "HIGH_INTENT"]


class ChatRequest(BaseModel):
    session_id: SessionId
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class ChatResponse(BaseModel):
    reply: str
    collected_fields: dict
    lead_ready: bool
    lead_status: Optional[str] = None


# ── Lead ──────────────────────────────────────────────────────────────
class LeadCreate(BaseModel):
    session_id: SessionId
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    email: EmailStr = Field(max_length=254)
    phone_whatsapp: Annotated[str, StringConstraints(strip_whitespace=True, min_length=7, max_length=32)]
    course_interest: RequiredText
    preferred_location: RequiredText
    current_education: RequiredText
    english_test_status: RequiredText
    budget_intake: RequiredText
    budget: Optional[RequiredText] = None
    intake: Optional[RequiredText] = None
    current_country_status: RequiredText
    # Accepted for compatibility, but the route computes the stored value.
    lead_status: LeadStatus = "LOW_INTENT"

    @field_validator("phone_whatsapp")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.fullmatch(r"\+?[0-9 ()-]+", value) or not 7 <= len(re.sub(r"\D", "", value)) <= 15:
            raise ValueError("Use a phone number with 7 to 15 digits")
        return value


class LeadOut(BaseModel):
    id: str
    session_id: str
    name: str
    email: str
    phone_whatsapp: str
    course_interest: str
    preferred_location: str
    current_education: str
    english_test_status: str
    budget_intake: str
    budget: Optional[str] = None
    intake: Optional[str] = None
    current_country_status: str
    lead_status: str
    created_at: str

    model_config = {"from_attributes": True}
