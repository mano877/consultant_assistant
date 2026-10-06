"""Match student preferences against the providers dataset."""

import json
import re
from pathlib import Path
from typing import Optional

_PROVIDERS_PATH = Path(__file__).resolve().parent.parent / "data" / "providers.json"

with open(_PROVIDERS_PATH) as f:
    PROVIDERS: list[dict] = json.load(f)


def prefers_postgraduate(current_education: Optional[str], course_interest: Optional[str]) -> bool:
    """Respect completed degrees unless the requested course is undergraduate."""
    education = current_education or ""
    bachelor_pattern = r"\b(?:bachelor(?:['’]s)?|bs|bsc|b\.s\.?|b\.sc\.?)\b"
    completed_bachelor = re.search(bachelor_pattern, education, re.I) and not re.search(
        r"\b(?:not|haven't|incomplete|pursuing|studying|enrolled|currently|ongoing)\b", education, re.I
    )
    undergraduate_requested = re.search(
        bachelor_pattern + r"|\bundergraduate\b", course_interest or "", re.I
    )
    return bool(completed_bachelor and not undergraduate_requested)


def match_providers(
    course_interest: Optional[str] = None,
    preferred_location: Optional[str] = None,
    ielts_overall: Optional[float] = None,
    current_education: Optional[str] = None,
) -> list[dict]:
    """Return up to two dataset matches by subject, location, IELTS and study level."""
    results = PROVIDERS
    if prefers_postgraduate(current_education, course_interest):
        results = [p for p in results if p["course"].startswith(("Master ", "Graduate "))]
        results = sorted(results, key=lambda p: not p["course"].startswith("Master "))
        # Broad computing enquiries cover related IT fields represented in the dataset.
        # Keep explicit specialisms and all later location/IELTS filters intact.
        broad_interest = re.sub(
            r"\b(?:postgraduate|graduate|graduates|options|programs|programmes|courses|masters|master|degree|in|of|for)\b",
            "", (course_interest or "").lower()
        ).strip()
        computing = r"\b(?:computer science|computing|cs|information technology|it)\b"
        if re.fullmatch(computing, broad_interest) or (
            not broad_interest and re.search(computing, current_education or "", re.I)
        ):
            course_interest = "IT"
        elif not broad_interest:
            # A degree alone in an unrelated field does not imply an IT preference.
            return []

    if course_interest:
        ci = re.sub(r"\bit\b", "information technology", course_interest.lower())
        ci = re.sub(r"\b(?:undergraduate|bs|bsc)\b", "bachelor", ci)
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
