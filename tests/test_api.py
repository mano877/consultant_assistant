"""Tests for the Achievement Education demo bot API."""

import json
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ── Force test env BEFORE importing the app ────────────────────────────
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory SQLite
os.environ["GROQ_API_KEY"] = "test-key-not-real"
os.environ["LEADS_ADMIN_TOKEN"] = "test-admin-token"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"

from app.database import Base, get_db
from app.models import Lead
from main import app

# ── Test DB setup ──────────────────────────────────────────────────────
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine)


def _override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

# Create tables once
Base.metadata.create_all(bind=engine)

client = TestClient(app)


# ── Helpers ────────────────────────────────────────────────────────────
def _fresh_session_id() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


def _scripted_reply(text):
    def invoke(messages):
        system = messages[0].content
        if system.startswith("You extract structured"):
            return MagicMock(content="{}")
        if system.startswith("You verify factual"):
            return MagicMock(content=json.dumps({"supported": True, "faq_indices": [6] if "26,000" in text else []}))
        return MagicMock(content=text)
    return invoke


def _mock_llm_reply(text: str):
    """Return a mock ChatGroq that always replies with `text`."""
    mock = MagicMock()
    mock.invoke.side_effect = _scripted_reply(text)
    return mock


# ── 1. Health check ───────────────────────────────────────────────────
class TestHealth:
    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ── 2. Normal consultation question ───────────────────────────────────
class TestNormalChat:
    @patch("app.services.agent._llm")
    def test_consultation_question_returns_ai_reply(self, mock_llm):
        mock_llm.invoke.side_effect = _scripted_reply("I'd be happy to help you explore IT courses in Australia! What is your highest qualification so far?")
        resp = client.post("/chat", json={
            "session_id": _fresh_session_id(),
            "message": "I'm interested in studying IT in Australia",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "reply" in body
        assert len(body["reply"]) > 10
        assert body["lead_ready"] is False
        assert isinstance(body["collected_fields"], dict)


# ── 3. Escalation phrase ──────────────────────────────────────────────
class TestEscalation:
    def test_visa_refused_triggers_escalation(self):
        resp = client.post("/chat", json={
            "session_id": _fresh_session_id(),
            "message": "I had a visa refused last year",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "consultant" in body["reply"].lower() or "review" in body["reply"].lower()
        assert body["lead_ready"] is False

    def test_complex_case_triggers_escalation(self):
        resp = client.post("/chat", json={
            "session_id": _fresh_session_id(),
            "message": "This is a complex case, I was deported before",
        })
        assert resp.status_code == 200
        body = resp.json()
        # Should mention consultant/follow-up
        assert any(kw in body["reply"].lower() for kw in ["consultant", "follow up", "review"])


# ── 4. Lead capture via POST /lead ────────────────────────────────────
class TestLeadCapture:
    def test_create_lead(self):
        payload = {
            "session_id": _fresh_session_id(),
            "name": "Test Student",
            "email": "test@example.com",
            "phone_whatsapp": "+61400000000",
            "course_interest": "Master of IT",
            "preferred_location": "Melbourne",
            "current_education": "Bachelor of CS",
            "english_test_status": "IELTS 6.5",
            "budget_intake": "AUD 35k, Feb 2026",
            "current_country_status": "India, student visa",
            "lead_status": "HIGH_INTENT",
        }
        resp = client.post("/lead", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Test Student"
        assert body["email"] == "test@example.com"
        assert body["lead_status"] == "HIGH_INTENT"
        assert "id" in body
        assert "created_at" in body


# ── 5. GET /leads returns captured leads ──────────────────────────────
class TestListLeads:
    def test_leads_endpoint_returns_array(self):
        resp = client.get("/leads", headers={"Authorization": "Bearer test-admin-token"})
        assert resp.status_code == 200
        leads = resp.json()
        assert isinstance(leads, list)
        # At least the lead we created in the previous test
        assert len(leads) >= 1

    def test_leads_contain_expected_fields(self):
        resp = client.get("/leads", headers={"Authorization": "Bearer test-admin-token"})
        leads = resp.json()
        lead = leads[0]
        required = [
            "id", "session_id", "name", "email", "phone_whatsapp",
            "course_interest", "preferred_location", "lead_status", "created_at",
        ]
        for field in required:
            assert field in lead, f"Missing field: {field}"


# ── 6. Session continuity ─────────────────────────────────────────────
class TestSessionContinuity:
    @patch("app.services.agent._llm")
    def test_session_retains_collected_fields(self, mock_llm):
        sid = _fresh_session_id()

        # First message — agent "collects" course_interest
        mock_llm.invoke.side_effect = _scripted_reply('Great, IT in Melbourne sounds perfect. What is your highest qualification?')
        resp1 = client.post("/chat", json={
            "session_id": sid,
            "message": "I want to study IT in Melbourne",
        })
        assert resp1.status_code == 200

        # Second message — agent "collects" current_education
        mock_llm.invoke.side_effect = _scripted_reply('Thanks! Have you taken IELTS or PTE yet?')
        resp2 = client.post("/chat", json={
            "session_id": sid,
            "message": "I have a Bachelor of Computer Science",
        })
        assert resp2.status_code == 200

        # Both messages share the same session_id — the store should exist
        body2 = resp2.json()
        assert isinstance(body2["collected_fields"], dict)

        # Verify the LLM was called three times per turn (extraction, reply, grounding), for 2 turns
        assert mock_llm.invoke.call_count == 6


# ── 7. Invalid / missing input ────────────────────────────────────────
class TestInputValidation:
    def test_empty_message_returns_422(self):
        resp = client.post("/chat", json={
            "session_id": "test-123",
            "message": "",
        })
        # Pydantic may accept empty string, or FastAPI may validate
        # Either 200 (accepted) or 422 (validation error) — both acceptable
        assert resp.status_code == 422

    def test_missing_session_id_returns_422(self):
        resp = client.post("/chat", json={
            "message": "Hello",
        })
        assert resp.status_code == 422

    def test_missing_message_returns_422(self):
        resp = client.post("/chat", json={
            "session_id": "test-123",
        })
        assert resp.status_code == 422

    def test_malformed_json_returns_422(self):
        resp = client.post(
            "/chat",
            content="not json at all",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_empty_body_returns_422(self):
        resp = client.post("/chat", json={})
        assert resp.status_code == 422

    def test_lead_missing_required_fields_returns_422(self):
        resp = client.post("/lead", json={"session_id": "test"})
        assert resp.status_code == 422

    def test_agent_error_returns_retryable_503(self):
        """If the LLM throws, the route returns a graceful fallback."""
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("Groq API down")
        with patch("app.services.agent._llm", mock_llm):
            resp = client.post("/chat", json={
                "session_id": _fresh_session_id(),
                "message": "Hello",
            })
        assert resp.status_code == 503
        body = resp.json()
        assert body["detail"]["code"] == "AI_UNAVAILABLE"
        assert body["detail"]["retryable"] is True
        assert "Groq API down" not in resp.text


# ── 8. Demo consultation scenarios ────────────────────────────────────
class TestDemoScenarios:
    """End-to-end scenario tests showcasing different conversation paths."""

    def test_visa_refusal_escalation_with_followup(self):
        """Scenario: Student with a previous visa refusal."""
        sid = _fresh_session_id()

        # Escalation trigger
        resp1 = client.post("/chat", json={
            "session_id": sid,
            "message": "I had a student visa refused 2 years ago. Can I still apply?",
        })
        assert resp1.status_code == 200
        body1 = resp1.json()
        assert any(kw in body1["reply"].lower() for kw in ["consultant", "follow up", "specialist"])
        assert body1["lead_ready"] is False

        # After escalation, agent should still work for normal questions
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = _scripted_reply('I understand your concern. Let me help you explore your options.')
        with patch("app.services.agent._llm", mock_llm):
            resp2 = client.post("/chat", json={
                "session_id": sid,
                "message": "What courses are available in Melbourne?",
            })
        assert resp2.status_code == 200
        assert len(resp2.json()["reply"]) > 10

    def test_budget_constrained_student(self):
        """Scenario: Student looking for affordable options."""
        sid = _fresh_session_id()

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = _scripted_reply("For budget-friendly options, I'd recommend Gold Coast or Adelaide — tuition starts around AUD 26,000-30,000 per year. The Gold Coast Institute of Technology offers a Bachelor of Information Systems at AUD 26,000/year. Shall I check specific programs for you?")
        with patch("app.services.agent._llm", mock_llm):
            resp = client.post("/chat", json={
                "session_id": sid,
                "message": "I want to study IT in Australia but my budget is tight, around AUD 25k per year",
            })
        assert resp.status_code == 200
        body = resp.json()
        assert "26,000" in body["reply"] or "25k" in body["reply"].lower() or "adelaide" in body["reply"].lower()

    def test_full_qualification_flow(self):
        """Scenario: Complete qualification flow from greeting to lead_ready."""
        sid = _fresh_session_id()

        scripted = [
            "Welcome! I'd love to help you find the right IT program. What's your highest qualification so far?",
            "Great! Have you taken IELTS or PTE? If so, what score did you get?",
            "Perfect. And which city are you leaning towards — Melbourne, Sydney, or somewhere else?",
            "Sounds good. What's your rough budget per year and when are you hoping to start?",
            "Excellent, I have some great options for you. Could I get your name, email, and phone number so a consultant can follow up?\n\nLEAD_READY",
        ]
        idx = 0
        def mock_invoke(messages):
            nonlocal idx
            if messages[0].content.startswith("You extract structured"):
                # The final turn supplies all remaining contact details.
                fields = {"course_interest": "IT", "preferred_location": "Melbourne",
                          "current_education": "Bachelor of Computer Science",
                          "english_test_status": "IELTS 6.5", "budget_intake": "AUD 35k, February 2027",
                          "current_country_status": "India"}
                if "Priya" in messages[-1].content:
                    fields.update(name="Priya Patel", email="priya@test.com", phone_whatsapp="+61412345678")
                return MagicMock(content=json.dumps(fields))
            if messages[0].content.startswith("You verify factual"):
                return MagicMock(content='{"supported": true}')
            reply = scripted[min(idx, len(scripted) - 1)]
            idx += 1
            return MagicMock(content=reply)

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = mock_invoke

        messages = [
            "Hi, I'm looking to study in Australia",
            "I have a Bachelor of Computer Science",
            "I got 6.5 in IELTS. I like Melbourne",
            "Around AUD 35k, starting February 2027",
            "I'm Priya Patel, email priya@test.com, phone +61412345678",
        ]

        for msg in messages:
            with patch("app.services.agent._llm", mock_llm):
                resp = client.post("/chat", json={
                    "session_id": sid,
                    "message": msg,
                })
            assert resp.status_code == 200

        body = resp.json()
        assert body["lead_ready"] is True
        assert isinstance(body["collected_fields"], dict)
