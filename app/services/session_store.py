"""In-memory session store — no persistence across restarts."""

from typing import Optional

_sessions: dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    """Return existing session or create a fresh one."""
    if session_id not in _sessions:
        _sessions[session_id] = {
            "history": [],
            "collected_fields": {
                "current_education": None,
                "course_interest": None,
                "english_test_status": None,
                "preferred_location": None,
                "budget_intake": None,
                "current_country_status": None,
                "name": None,
                "email": None,
                "phone_whatsapp": None,
            },
            "status": "active",
        }
    return _sessions[session_id]


def update_session(session_id: str, **kwargs) -> dict:
    """Shallow-merge keys into the session dict."""
    session = get_session(session_id)
    session.update(kwargs)
    return session


def reset_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
