"""Intake omission, independent updates, and backward-compatible persistence."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tests.test_api import client, _fresh_session_id
from tests.test_predeployment import valid_lead
from app.services.agent import _extract_updated_fields
from app.services.intake import extract_intake, merge_budget_intake
from app.services.lead_scoring import infer_lead_status


CASES = [
    ("February 2027", "February 2027"),
    ("Feb 2027", "Feb 2027"),
    ("February intake", "February intake"),
    ("July 2027 intake", "July 2027 intake"),
    ("next February", "next February"),
    ("next July", "next July"),
    ("2027 intake", "2027 intake"),
    ("I want to start in February 2027", "February 2027"),
    ("I'm planning for the July intake", "July intake"),
    ("September intake", "September intake"),
]


@pytest.mark.parametrize("phrase,expected", CASES)
@pytest.mark.parametrize("embedded", [False, True], ids=["standalone", "natural-message"])
def test_first_mention_survives_llm_omission(phrase, expected, embedded):
    message = phrase if not embedded else (
        "I have a Bachelor of Computer Science and want Master of IT in Melbourne. "
        "I have IELTS 7, my budget is AUD 36,000 per year for " + phrase +
        ". I'm in Pakistan with no Australian visa."
    )
    # Reproduce the observed failure: model extracts budget, omits intake.
    extracted = {"budget": "AUD 36,000 per year", "course_interest": "Master of IT",
                 "english_test_status": "IELTS 7"}
    with patch("app.services.agent._llm") as llm:
        llm.invoke.return_value = MagicMock(content=json.dumps(extracted))
        result = _extract_updated_fields({}, message)
    assert result["intake"] == expected
    assert result["budget"] == "AUD 36,000 per year"
    assert result["course_interest"] == "Master of IT"
    assert result["english_test_status"] == "IELTS 7"
    assert expected in result["budget_intake"]
    assert infer_lead_status(result) == "HIGH_INTENT"


@pytest.mark.parametrize("message", [
    "My budget is AUD 2027", "My budget is $2027", "I have AUD 36,000 per year",
    "I took IELTS in February 2027", "I graduated in July 2027",
    "My birthday is in September", "Do you offer a February intake?",
    "What are the July 2027 intake deadlines?", "I do not want February 2027 intake",
    "I want to start in February or July", "I want to study IT in Melbourne",
    "I completed my degree in 2027", "My passport expires in February 2027",
])
def test_other_dates_questions_and_budget_do_not_invent_intake(message):
    assert extract_intake(message) is None
    with patch("app.services.agent._llm") as llm:
        llm.invoke.return_value = MagicMock(content='{"intake":"February 2027"}')
        result = _extract_updated_fields({}, message)
    assert "intake" not in result


def test_budget_and_intake_updates_are_independent():
    fields = merge_budget_intake({}, {"budget": "AUD 36,000 per year"}, "I want to start in February 2027")
    fields = merge_budget_intake(fields, {"budget": "AUD 40,000"}, "My budget is now AUD 40,000")
    assert fields["intake"] == "February 2027"
    fields = merge_budget_intake(fields, {}, "I'm planning for the July intake")
    assert fields["budget"] == "AUD 40,000"
    assert fields["intake"] == "July intake"
    fields = merge_budget_intake(fields, {}, "My intake is not decided")
    assert fields["intake"] == "Not decided"
    assert infer_lead_status({**fields, "english_test_status": "IELTS 7"}) == "MEDIUM_INTENT"


def test_separate_intake_controls_scoring_not_budget_year():
    assert infer_lead_status({"budget": "AUD 2027", "intake": None,
                              "budget_intake": "2027", "english_test_status": "Not taken"}) == "LOW_INTENT"


def test_separate_signals_survive_lead_save_and_retrieval():
    payload = valid_lead()
    payload.update(budget="AUD 36,000 per year", intake="next February",
                   budget_intake="AUD 36,000 per year, next February", english_test_status="IELTS 7")
    response = client.post("/lead", json=payload)
    assert response.status_code == 200
    saved = response.json()
    assert saved["budget"] == payload["budget"]
    assert saved["intake"] == "next February"
    assert saved["session_id"] == payload["session_id"]
    assert saved["lead_status"] == "HIGH_INTENT"
    assert saved in client.get("/leads", headers={"Authorization": "Bearer test-admin-token"}).json()


@pytest.mark.parametrize("combined", ["AUD 35k, Feb 2027", "AUD 35k Feb 2027"])
def test_legacy_lead_contract_still_works(combined):
    payload = valid_lead()
    payload["budget_intake"] = combined
    saved = client.post("/lead", json=payload).json()
    assert saved["budget"] == "AUD 35k"
    assert saved["intake"] == "Feb 2027"
    assert saved["budget_intake"] == payload["budget_intake"]


def test_intake_failure_does_not_override_unrelated_known_fields():
    with patch("app.services.agent._llm") as llm:
        llm.invoke.return_value = MagicMock(content='{}')
        known = {"name": "Student", "course_interest": "IT", "budget": "AUD 35k", "intake": "February 2027"}
        updated = {**known, **_extract_updated_fields(known, "Thanks")}
    assert updated["name"] == "Student"
    assert updated["course_interest"] == "IT"
    assert updated["intake"] == "February 2027"
