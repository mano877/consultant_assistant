"""Manual conversation simulation — shows real request/response pairs.

The LLM is mocked with scripted replies to demonstrate the full flow
without needing a live Groq API key. All routing, session management,
escalation detection, provider matching, and lead capture are real.
"""

import json
import os
import sys

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["GROQ_API_KEY"] = "test-key"

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models import Lead
from app.services.session_store import reset_session
from main import app

# ── Test DB ────────────────────────────────────────────────────────────
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)

def _override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _override_get_db
Base.metadata.create_all(bind=engine)
client = TestClient(app)

SID = "demo-conv-001"

# ── Scripted LLM replies (in order) ───────────────────────────────────
SCRIPTED_REPLIES = [
    # Turn 1 — agent asks about education
    (
        "That's a great choice! Australia has excellent IT programs. "
        "To help find the right fit, could you tell me what your highest "
        "qualification is so far? For example, do you have a bachelor's degree?"
    ),
    # Turn 2 — agent asks about English test
    (
        "Perfect, a Bachelor of Computer Science gives you strong options. "
        "Have you taken IELTS or PTE yet? If so, what was your score? "
        "This helps me match you with programs you qualify for."
    ),
    # Turn 3 — agent asks about location + budget + provider recs
    (
        "IELTS 6.5 is solid — you meet the requirements for most master's "
        "programs. Looking at Melbourne options, I'd recommend the Master of "
        "Information Technology at Australian Technology Institute "
        "(AUD 36,000/year, 24 months). What's your budget range and "
        "preferred start date?"
    ),
    # Turn 4 — agent asks for contact details, marks lead ready
    (
        "Great, that timeline works well. I have some excellent matches for "
        "you. Could you share your name, email, and phone or WhatsApp number? "
        "I'll have a consultant follow up with personalised next steps "
        "and help with your application.\n\nLEAD_READY"
    ),
]

reply_index = 0


# ── Run the conversation ──────────────────────────────────────────────
def run():
    global reply_index
    reply_index = 0
    reset_session(SID)

    conversation = [
        "I'm interested in studying in Australia.",
        "I have a Bachelor of Computer Science.",
        "I got 6.5 in IELTS. I prefer Melbourne. Budget around AUD 35k, starting Feb 2027.",
        "My name is Rahul Sharma, email rahul@example.com, phone +91-9876543210.",
    ]

    print("=" * 70)
    print("MANUAL CONVERSATION TEST")
    print("=" * 70)

    for i, msg in enumerate(conversation, 1):
        print(f"\n{'-' * 70}")
        print(f"TURN {i}")
        print(f"{'=' * 70}")
        print(f"\n  >>> USER: {msg}")

        # Build a mock LLM that returns scripted replies
        mock_llm = MagicMock()

        def _make_invoke(idx):
            def _invoke(messages):
                return MagicMock(content=SCRIPTED_REPLIES[idx])
            return _invoke

        mock_llm.invoke.side_effect = _make_invoke(i - 1)

        with patch("app.services.agent._llm", mock_llm):
            resp = client.post("/chat", json={
                "session_id": SID,
                "message": msg,
            })

        body = resp.json()
        print(f"\n  <<< BOT (status {resp.status_code}):")
        # Word-wrap the reply
        for line in body["reply"].split("\n"):
            print(f"      {line}")

        fields = {k: v for k, v in body["collected_fields"].items() if v}
        if fields:
            print(f"\n  [collected_fields]:")
            for k, v in fields.items():
                print(f"      {k}: {v}")
        print(f"  [lead_ready]: {body['lead_ready']}")

    # ── Verify lead can be captured ───────────────────────────────────
    print(f"\n{'-' * 70}")
    print("LEAD CAPTURE")
    print(f"{'=' * 70}")
    lead_payload = {
        "session_id": SID,
        "name": "Rahul Sharma",
        "email": "rahul@example.com",
        "phone_whatsapp": "+91-9876543210",
        "course_interest": "Master of IT",
        "preferred_location": "Melbourne",
        "current_education": "Bachelor of Computer Science",
        "english_test_status": "IELTS 6.5",
        "budget_intake": "AUD 35k/year, Feb 2027",
        "current_country_status": "India, student visa",
        "lead_status": "HIGH_INTENT",
    }
    print(f"\n  >>> POST /lead: {json.dumps(lead_payload, indent=6)}")
    lead_resp = client.post("/lead", json=lead_payload)
    lr = lead_resp.json()
    print(f"\n  <<< STATUS: {lead_resp.status_code}")
    print(f"      Lead ID:     {lr['id']}")
    print(f"      Created:     {lr['created_at']}")
    print(f"      Lead Status: {lr['lead_status']}")

    # ── Verify via GET /leads ─────────────────────────────────────────
    print(f"\n{'-' * 70}")
    print("VERIFY LEADS (GET /leads)")
    print(f"{'=' * 70}")
    leads_resp = client.get("/leads")
    leads = leads_resp.json()
    print(f"\n  <<< STATUS: {leads_resp.status_code}")
    print(f"      Total leads: {len(leads)}")
    for l in leads:
        print(f"      - {l['name']} ({l['email']}) | {l['lead_status']} | {l['course_interest']}")

    print(f"\n{'=' * 70}")
    print("CONVERSATION TEST COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run()
