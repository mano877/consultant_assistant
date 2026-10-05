"""Chat endpoint — orchestrates escalation, session, and agent."""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.services.agent import run_agent
from app.services.escalation import ESCALATION_REPLY, check_escalation
from app.services.session_store import get_session

logger = logging.getLogger(__name__)
router = APIRouter()

FALLBACK_REPLY = (
    "I'm sorry, I'm having a brief technical issue. Please try again "
    "in a moment, or a consultant will be happy to help you directly."
)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session = get_session(req.session_id)

    # ── Escalation check (before LLM) ────────────────────────────────
    escalated = check_escalation(req.message)

    if escalated:
        session["history"].append({"role": "user", "content": req.message})
        collected = session.get("collected_fields", {})

        return ChatResponse(
            reply=ESCALATION_REPLY,
            collected_fields=collected,
            lead_ready=False,
        )

    # ── Normal agent flow (with error handling) ───────────────────────
    try:
        result = run_agent(req.session_id, req.message)
    except Exception as exc:
        logger.exception("Agent error for session %s", req.session_id)
        raise HTTPException(status_code=503, detail={
            "code": "AI_UNAVAILABLE", "message": FALLBACK_REPLY, "retryable": True,
        }) from None

    return ChatResponse(
        reply=result["reply"],
        collected_fields=result["collected_fields"],
        lead_ready=result["lead_ready"],
        lead_status=result["lead_status"],
    )
