"""Shared server-side scoring for chat qualification and saved leads."""

import re


def completed_english_test(value: str) -> bool:
    text = " ".join(value.lower().replace("’", "'").split())
    if re.search(r"\b(not|no|never|haven't|hasn't|didn't|yet|pending|awaiting|waiting|booked|scheduled|planning|plan|target|targeting|aim|aiming|hope|registered|will|intend|intending|preparing|required|need|unknown|unsure)\b", text):
        return False
    # A test name alone does not mean the test was completed.
    return bool(
        re.search(r"\b(ielts|pte|toefl|english test)\b", text)
        and re.search(r"\b(\d+(?:\.\d+)?|completed|taken|passed|scored)\b", text)
    )


def has_intake_timing(value: str) -> bool:
    text = value.lower()
    # Amounts alone (including AUD 2027) are not evidence of an intake.
    text = re.sub(r"\b(?:aud|usd|gbp|eur|budget)\s*[:=]?\s*\d[\d,.]*\s*k?\b|[$£€]\s*\d[\d,.]*", "", text)
    if re.search(r"\b(undecided|unsure|unknown|not decided|not sure|no intake|no date|not specified)\b", text):
        return False
    return bool(re.search(
        r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|20\d{2})\b"
        r"|\b(next|this)\s+(year|month|semester|intake|spring|summer|autumn|fall|winter)\b"
        r"|\b(in|within)\s+\d+\s+months?\b", text
    ))


def infer_lead_status(fields: dict) -> str:
    english = completed_english_test(fields.get("english_test_status") or "")
    timing = has_intake_timing(fields.get("intake") or "") if "intake" in fields else has_intake_timing(fields.get("budget_intake") or "")
    if english and timing:
        return "HIGH_INTENT"
    if english or timing:
        return "MEDIUM_INTENT"
    return "LOW_INTENT"
