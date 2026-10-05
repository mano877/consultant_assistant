"""Match student preferences against the providers dataset."""

import json
import re
from pathlib import Path
from typing import Optional

_PROVIDERS_PATH = Path(__file__).resolve().parent.parent / "data" / "providers.json"

with open(_PROVIDERS_PATH) as f:
    PROVIDERS: list[dict] = json.load(f)


def match_providers(
    course_interest: Optional[str] = None,
    preferred_location: Optional[str] = None,
    ielts_overall: Optional[float] = None,
) -> list[dict]:
    """Return top 1-2 matching providers as plain dicts.

    Matching rules (all optional — fewer filters means broader match):
    - course_interest → words match course/tags (IT expands to information technology)
    - preferred_location → location contains (case-insensitive)
    - ielts_overall    → entry_requirements.ielts_overall <= student's score
    """
    results = PROVIDERS

    if course_interest:
        ci = re.sub(r"\bit\b", "information technology", course_interest.lower())
        words = set(re.findall(r"[a-z]+", ci)) - {"of", "in", "a", "the", "study"}
        results = [
            p for p in results
            if words and words <= set(re.findall(
                r"[a-z]+", re.sub(r"\bit\b", "information technology",
                    p["course"].lower() + " " + " ".join(p.get("tags", [])).lower())
            ))
        ]

    if preferred_location:
        pl = preferred_location.lower()
        results = [
            p for p in results
            if pl in p.get("location", "").lower()
        ]

    if ielts_overall is not None:
        results = [
            p for p in results
            if p.get("entry_requirements", {}).get("ielts_overall", 0) <= ielts_overall
        ]

    return results[:2]
