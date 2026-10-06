"""Natural wording and qualification-aware, dataset-only recommendations."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tests.test_api import _fresh_session_id
from app.services.agent import FAQ_DATA, _grounded_reply, run_agent
from app.services.provider_matcher import PROVIDERS, match_providers
from app.services.session_store import get_session


@pytest.mark.parametrize("education", ["BS Computer Science", "BSc Computer Science", "Bachelor's degree", "Completed Bachelor of Computer Science"])
def test_graduates_get_postgraduate_records_first(education):
    matches = match_providers("IT", current_education=education)
    assert len(matches) == 2
    assert all(p in PROVIDERS and p["course"].startswith("Master ") for p in matches)
    sydney = match_providers("IT", "Sydney", current_education=education)
    assert [p["course"] for p in sydney] == ["Graduate Diploma of Information Technology"]


@pytest.mark.parametrize("interest", ["Bachelor of Computer Science", "undergraduate computer science", "BS Computer Science"])
def test_explicit_undergraduate_request_is_respected(interest):
    matches = match_providers(interest, "Sydney", current_education="BS Computer Science")
    assert [p["course"] for p in matches] == ["Bachelor of Computer Science"]


@pytest.mark.parametrize("education", [None, "Year 12", "Currently studying BS Computer Science", "Bachelor not completed"])
def test_no_completed_degree_keeps_existing_options(education):
    assert match_providers("IT", "Sydney", current_education=education)[0]["course"].startswith("Bachelor ")


def test_no_postgraduate_match_does_not_fall_back_to_undergraduate():
    assert match_providers("IT", "Gold Coast", current_education="BS Computer Science") == []
    assert match_providers("Space Medicine", current_education="BS Computer Science") == []


@pytest.mark.parametrize("interest", [None, "Computer Science", "graduate options", "postgraduate programs"])
@pytest.mark.parametrize("city,course", [
    ("Melbourne", "Master of Data Science"),
    ("Brisbane", "Master of Cybersecurity"),
    ("Adelaide", "Master of Software Engineering"),
    ("Perth", "Master of Artificial Intelligence"),
])
def test_computer_science_graduates_match_related_dataset_programs(interest, city, course):
    matches = match_providers(interest, city, current_education="BS in Computer Science")
    assert course in [p["course"] for p in matches]
    assert all(p in PROVIDERS and not p["course"].startswith("Bachelor") for p in matches)


@pytest.mark.parametrize("interest", [None, "Computer Science", "graduate options"])
def test_exact_graduate_enquiry_matches_without_a_city(interest):
    message = "I have a BS in Computer Science. What options do I have for graduates?"
    fields = {"current_education": "BS in Computer Science"}
    if interest:
        fields["course_interest"] = interest

    def invoke(messages):
        if messages[0].content.startswith("You extract structured"):
            return MagicMock(content=json.dumps(fields))
        if messages[0].content.startswith("You verify factual"):
            payload = json.loads(messages[1].content)
            assert payload["providers"]
            assert all(p in PROVIDERS and p["course"].startswith("Master") for p in payload["providers"])
            return MagicMock(content='{"supported": true, "provider_indices": [0, 1]}')
        return MagicMock(content="Explore postgraduate options.")

    with patch("app.services.agent._llm") as llm:
        llm.invoke.side_effect = invoke
        result = run_agent(_fresh_session_id(), message)
    assert "Master of Information Technology" in result["reply"]
    assert "Master of Data Science" in result["reply"]
    assert "Bachelor of" not in result["reply"]
    assert "don't have enough information" not in result["reply"]
    assert "preferred_location" not in result["collected_fields"]


def test_related_matching_preserves_specific_constraints():
    assert match_providers("Space Medicine", current_education="BS Computer Science") == []
    assert match_providers("Computer Science", "London", current_education="BS Computer Science") == []
    assert match_providers("Computer Science", "Brisbane", 5.0, "BS Computer Science") == []
    assert match_providers("Cybersecurity", "Melbourne", current_education="BS Computer Science") == []


def test_natural_preambles_preserve_source_facts():
    with patch("app.services.agent._llm") as llm:
        llm.invoke.return_value = MagicMock(content='{"supported": true, "provider_indices": [0], "faq_indices": [5]}')
        reply = _grounded_reply("ignored", PROVIDERS[:1], {})
    assert "Based on the available information, here are some options you could explore:" in reply
    assert "Here's what may help:" in reply
    assert FAQ_DATA[5]["answer"] in reply
    assert "36,000" in reply
    assert "Our available reference information says:" not in reply


def test_degree_is_remembered_and_grounding_cannot_reintroduce_undergraduate_options():
    sid = _fresh_session_id()
    fields = {"current_education": "BS Computer Science", "course_interest": "IT", "preferred_location": "Sydney"}

    def invoke(messages):
        if messages[0].content.startswith("You extract structured"):
            return MagicMock(content=json.dumps(fields if not get_session(sid)["history"] else {}))
        if messages[0].content.startswith("You verify factual"):
            payload = json.loads(messages[1].content)
            assert [p["course"] for p in payload["providers"]] == ["Graduate Diploma of Information Technology"]
            assert not any("Bachelor of Computer Science" in f["answer"] for f in payload["faq"])
            assert any("require a Bachelor degree" in f["answer"] for f in payload["faq"])
            return MagicMock(content='{"supported": true, "provider_indices": [0], "faq_indices": []}')
        return MagicMock(content="Consider an invented MSc or a Bachelor of Computer Science")

    with patch("app.services.agent._llm") as llm:
        llm.invoke.side_effect = invoke
        for message in ["I completed BS Computer Science. Recommend IT courses in Sydney.", "What would you suggest?"]:
            reply = run_agent(sid, message)["reply"]
            assert "Graduate Diploma of Information Technology" in reply
            assert "Bachelor of Computer Science" not in reply
            assert "invented" not in reply
            assert "Have you taken IELTS or PTE yet?" in reply
    assert all(get_session(sid)["collected_fields"][key] == value for key, value in fields.items())
    assert len(get_session(sid)["history"]) == 4
