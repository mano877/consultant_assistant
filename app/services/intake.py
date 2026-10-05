"""Conservative extraction of student-supplied intake timing.

Keep relative dates verbatim: 'next February' must not acquire an invented year.
This operates on student text only, never provider records or assistant replies.
"""

import re

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
TIMING = re.compile(
    rf"\b(?:(?:(?:next|this)\s+)?{MONTH}(?:\s+20\d{{2}})?(?:\s+intake)?"
    r"|20\d{2}(?:\s+intake)?|(?:next|this)\s+(?:year|month|semester|intake|spring|summer|autumn|fall|winter)"
    r"|(?:in|within)\s+\d+\s+months?)\b", re.I
)
UNDECIDED = re.compile(
    r"\b(?:intake|start date)\s+(?:is\s+)?(?:still\s+)?(?:undecided|unknown|not decided|not sure)\b"
    r"|\b(?:not sure|undecided|haven't decided|have not decided)\s+(?:about\s+)?(?:my\s+)?(?:intake|start date)\b",
    re.I,
)


def extract_intake(message: str) -> str | None:
    """Return explicit timing, abstaining on questions, negations and other dates."""
    if UNDECIDED.search(message):
        return "Not decided"
    candidates = []
    for match in TIMING.finditer(message):
        # Clause context prevents an IELTS/graduation date becoming an intake.
        boundary = r"[.!?;\n]|,(?!\d)|\bbut\b|\band\b"
        before = re.split(boundary, message[:match.start()], flags=re.I)[-1]
        after = re.split(boundary, message[match.end():], flags=re.I)[0]
        clause = before + match.group() + after
        if re.search(r"(?:\b(?:AUD|USD|GBP|EUR|budget)\s*[:=]?\s*|[$£€]\s*)$", before, re.I):
            continue
        if re.search(r"\b(?:not|no|never|don't|do not|can't|cannot|won't|rather than)\b", before, re.I):
            continue
        if re.search(r"\b(?:IELTS|PTE|TOEFL|exam|test|graduated|graduation|completed|birthday|born|passport|visa expires)\b", before, re.I):
            continue
        if re.search(r"\b(?:do you|does|is there|are there|available|offer|deadline|when|what)\b", clause, re.I):
            continue
        raw = match.group()
        standalone = message.strip(" .!\n").lower() == raw.lower()
        explicit = bool(re.search(r"\b(?:intake|start|starting|begin|commence|planning|aiming|targeting|for)\b", before, re.I))
        # A bare month in unrelated prose is not evidence of the intended intake.
        if standalone or explicit or re.match(r"\s*intake\b", after, re.I):
            candidates.append(raw)
    # Multiple different options are not a confirmed preference.
    unique = list(dict.fromkeys(candidates))
    return unique[0] if len(unique) == 1 else None


def split_legacy(value: str) -> tuple[str | None, str | None]:
    """Read already-collected legacy data without confusing currency with a year."""
    if not value or value.lower() == "not specified":
        return None, None
    timing = extract_intake(value)
    if timing is None:
        # Legacy combined values commonly used a comma instead of 'starting'.
        for part in re.split(r"[,;] (?=[A-Za-z]|20\d{2}\b)", value):
            timing = extract_intake(part)
            if timing:
                break
    if timing is None and not re.search(r"\b(?:undecided|unknown|not decided|not specified)\b", value, re.I):
        for match in TIMING.finditer(value):
            if not re.search(r"(?:\b(?:AUD|USD|GBP|EUR|budget)\s*[:=]?\s*|[$£€]\s*)$", value[:match.start()], re.I):
                timing = match.group()
                break
    budget = value.replace(timing, "").strip(" ,;") if timing else value
    budget = re.sub(r"(?:[,;]\s*)?(?:intake|starting|start|for)\s*[:=]?\s*$", "", budget, flags=re.I).strip(" ,;")
    return budget or None, timing


def merge_budget_intake(known: dict, extracted: dict, message: str) -> dict:
    """Update the two signals independently; compose the legacy wire field."""
    legacy_budget, legacy_intake = split_legacy(known.get("budget_intake") or "")
    budget = known.get("budget") or legacy_budget
    intake = known.get("intake") or legacy_intake
    # The LLM still extracts budget and all unrelated facts as before.
    new_budget = extracted.get("budget")
    if not new_budget and extracted.get("budget_intake"):
        new_budget, _ = split_legacy(extracted["budget_intake"])
    if new_budget:
        budget = new_budget
    stated_intake = extract_intake(message)
    if stated_intake:
        intake = stated_intake
    result = {}
    if budget:
        result["budget"] = budget
    if intake:
        result["intake"] = intake
    if budget or intake:
        result["budget_intake"] = ", ".join(v for v in (budget, intake) if v)
    return result
