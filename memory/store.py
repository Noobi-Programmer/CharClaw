"""
memory/store.py - Persistent command history and key-value store.

Data is written to memory/journal.json.
History is capped at 200 entries to avoid unbounded growth.
"""

import json
import os
from datetime import datetime

_STORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "journal.json")
_MAX_HISTORY = 200

_defaults = {
    "history": [],
    "kv": {},
    "session_count": 0,
}

_data: dict | None = None


def _load() -> dict:
    global _data
    if _data is not None:
        return _data
    if os.path.exists(_STORE_FILE):
        try:
            with open(_STORE_FILE) as f:
                _data = json.load(f)
        except Exception:
            _data = dict(_defaults)
    else:
        _data = dict(_defaults)
    return _data


def _save():
    os.makedirs(os.path.dirname(_STORE_FILE), exist_ok=True)
    with open(_STORE_FILE, "w") as f:
        json.dump(_data, f, indent=2)


# ── public API ────────────────────────────────────────────────────────────────

def remember_command(user_input: str, command: str, success: bool):
    d = _load()
    d["history"].append({
        "input":   user_input[:120],
        "command": command[:120],
        "success": success,
        "time":    datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    d["history"] = d["history"][-_MAX_HISTORY:]
    _save()


def get_history(limit: int = 20) -> list[dict]:
    return _load()["history"][-limit:]


def kv_set(key: str, value):
    d = _load()
    d["kv"][key] = value
    _save()


def kv_get(key: str, default=None):
    return _load()["kv"].get(key, default)


def tick_session():
    d = _load()
    d["session_count"] = d.get("session_count", 0) + 1
    _save()


def session_count() -> int:
    return _load().get("session_count", 0)
