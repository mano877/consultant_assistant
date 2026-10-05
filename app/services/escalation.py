"""Pre-LLM escalation check — short-circuits with a fixed response."""

import json
from pathlib import Path

_PHRASES_PATH = Path(__file__).resolve().parent.parent / "data" / "escalation_phrases.json"

with open(_PHRASES_PATH) as f:
    ESCALATION_PHRASES: list[str] = json.load(f)

ESCALATION_REPLY = (
    "I appreciate you sharing that with me — I understand this can feel "
    "overwhelming. Your situation deserves personalised attention from "
    "one of our experienced consultants who specialize in these cases. "
    "A member of our team will be in touch shortly to discuss your "
    "options. In the meantime, I can still help you explore courses "
    "and gather your details so we can hit the ground running."
)


def check_escalation(message: str) -> bool:
    """Return True if the message triggers an escalation phrase."""
    lower = message.lower()
    return any(phrase in lower for phrase in ESCALATION_PHRASES)
