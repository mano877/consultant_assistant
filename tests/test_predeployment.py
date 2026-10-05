"""Regression coverage for the limited pre-deployment fixes."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tests.test_api import client, _fresh_session_id
from app.services.agent import run_agent
from app.services.lead_scoring import infer_lead_status
from app.services.provider_matcher import match_providers
from app.services.session_store import get_session


def valid_lead():
    return dict(session_id=_fresh_session_id(), name="Test Student", email="test@example.com",
                phone_whatsapp="+61 (400) 000-000", course_interest="Master of IT",
                preferred_location="Melbourne", current_education="Bachelor of CS",
                english_test_status="Not taken IELTS", budget_intake="AUD 35000",
                current_country_status="Pakistan", lead_status="HIGH_INTENT")


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer wrong"}, {"Authorization": "Basic abc"}])
def test_lead_access_requires_admin(headers):
    assert client.get("/leads", headers=headers).status_code == 401


def test_unconfigured_admin_fails_closed():
    with patch("app.routes.lead.LEADS_ADMIN_TOKEN", ""):
        assert client.get("/leads", headers={"Authorization": "Bearer test-admin-token"}).status_code == 401


def test_server_controls_score_and_authorized_retrieval():
    payload = valid_lead()
    saved = client.post("/lead", json=payload)
    assert saved.status_code == 200
    assert saved.json()["lead_status"] == "LOW_INTENT"
    rows = client.get("/leads", headers={"Authorization": "Bearer test-admin-token"}).json()
    assert saved.json() in rows


@pytest.mark.parametrize("origin,expected", [("http://localhost:3000", 200), ("http://127.0.0.1:3000", 200), ("https://untrusted.example", 400)])
def test_cors_preflight(origin, expected):
    response = client.options("/chat", headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert response.status_code == expected
    assert response.headers.get("access-control-allow-origin") == (origin if expected == 200 else None)


@pytest.mark.parametrize("key,value", [
    ("session_id", " "), ("session_id", "x" * 129), ("session_id", "bad/session"),
    ("name", " "), ("name", "x" * 121), ("email", "not-an-email"),
    ("phone_whatsapp", "abcdefghi"), ("phone_whatsapp", "+123"),
    ("phone_whatsapp", "1" * 16), ("course_interest", " "),
    ("budget_intake", "x" * 501), ("lead_status", "ADMIN"),
])
def test_invalid_leads_rejected(key, value):
    payload = valid_lead()
    payload[key] = value
    assert client.post("/lead", json=payload).status_code == 422


@pytest.mark.parametrize("status", ["Not taken IELTS", "not taken yet", "I haven't taken IELTS", "IELTS pending", "IELTS scheduled", "IELTS target 6.5", "No IELTS or PTE", "Not completed", "Awaiting IELTS result", "Yet to take IELTS, aiming for 6.5", "Will take IELTS 6.5", "IELTS required 6.5"])
def test_negative_english_is_not_completion(status):
    assert infer_lead_status({"english_test_status": status, "budget_intake": "AUD 35000"}) == "LOW_INTENT"
    assert infer_lead_status({"english_test_status": status, "budget_intake": "AUD 35000, February 2027"}) == "MEDIUM_INTENT"


@pytest.mark.parametrize("english,timing,expected", [
    ("IELTS 6.5", "AUD 35000", "MEDIUM_INTENT"),
    ("PTE 58", "February 2027", "HIGH_INTENT"),
    ("IELTS completed", "next year", "HIGH_INTENT"),
    ("Not specified", "AUD 2027", "LOW_INTENT"),
    ("Not specified", "2027", "MEDIUM_INTENT"),
])
def test_scoring_distinguishes_budget_and_intake(english, timing, expected):
    assert infer_lead_status({"english_test_status": english, "budget_intake": timing}) == expected


def test_current_fields_are_used_before_matching_and_remembered():
    sid = _fresh_session_id()
    extracted = {"course_interest": "Master of IT", "preferred_location": "Melbourne", "english_test_status": "IELTS 6.5"}
    def invoke(messages):
        if messages[0].content.startswith("You extract structured"):
            return MagicMock(content=json.dumps(extracted))
        if messages[0].content.startswith("You verify factual"):
            return MagicMock(content='{"supported": true, "provider_indices": [0]}')
        assert "Australian Technology Institute" in messages[0].content
        assert '"tuition_aud_per_year": 36000' in messages[0].content
        return MagicMock(content="The available record lists **Australian Technology Institute** at AUD 36,000 per year.")
    with patch("app.services.agent._llm") as llm:
        llm.invoke.side_effect = invoke
        result = run_agent(sid, "Master of IT in Melbourne; IELTS 6.5")
    assert "Australian Technology Institute" in result["reply"]
    assert "36,000" in result["reply"]
    assert result["collected_fields"] == extracted
    assert len(get_session(sid)["history"]) == 2


def test_unknown_course_has_no_invented_alternative():
    assert match_providers("Space Medicine", "London") == []


def test_broad_it_and_full_course_names_still_match():
    assert match_providers("IT", "Brisbane")[0]["course"] == "Master of Cybersecurity"
    assert match_providers("Master of IT", "Melbourne")[0]["course"] == "Master of Information Technology"


def test_unsupported_reply_is_not_shown_or_saved():
    sid = _fresh_session_id()
    with patch("app.services.agent._llm") as llm:
        llm.invoke.side_effect = [MagicMock(content="{}"), MagicMock(content="Invented University costs AUD 100."), MagicMock(content='{"supported": false}')]
        result = run_agent(sid, "Give me a cheap university")
    assert "Invented" not in result["reply"]
    assert "available records" in result["reply"]
    assert "Invented" not in json.dumps(get_session(sid))


@pytest.mark.parametrize("failure_at", [0, 1, 2])
def test_ai_failure_is_retryable_and_does_not_commit_partial_turn(failure_at):
    sid = _fresh_session_id()
    responses = [MagicMock(content="{}"), MagicMock(content="Hello!"), MagicMock(content='{"supported": true}')]
    responses[failure_at] = RuntimeError("secret internal error")
    with patch("app.services.agent._llm") as llm:
        llm.invoke.side_effect = responses
        response = client.post("/chat", json={"session_id": sid, "message": "Hello"})
    assert response.status_code == 503
    assert response.json()["detail"]["retryable"] is True
    assert "secret internal" not in response.text
    assert get_session(sid)["history"] == []


def test_generated_claims_never_render_even_if_selector_claims_supported():
    sid = _fresh_session_id()
    with patch("app.services.agent._llm") as llm:
        llm.invoke.side_effect = [MagicMock(content="{}"),
            MagicMock(content="A passport valid for the whole study period is required. Invented University costs AUD 100."),
            MagicMock(content='{"supported": true, "faq_indices": [5]}')]
        result = run_agent(sid, "What documents do I need?")
    assert "valid for the whole" not in result["reply"]
    assert "Invented University" not in result["reply"]
    assert "AUD 100" not in result["reply"]
    assert "transcripts, English test results, passport" in result["reply"]


def test_invalid_reference_is_rejected_not_rendered():
    with patch("app.services.agent._llm") as llm:
        llm.invoke.side_effect = [MagicMock(content="{}"), MagicMock(content="Hello"),
                                 MagicMock(content='{"supported": true, "provider_indices": [999]}')]
        response = client.post("/chat", json={"session_id": _fresh_session_id(), "message": "Hello"})
    assert response.status_code == 503
