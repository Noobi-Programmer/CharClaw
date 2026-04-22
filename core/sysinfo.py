"""
core/sysinfo.py - System capability detection.

Probes for installed tools once at import time.
All results are cached — zero overhead after first call.
"""

import shutil

_cache: dict[str, str | None] = {}


def which(app: str) -> str | None:
    if app not in _cache:
        _cache[app] = shutil.which(app)
    return _cache[app]


def exists(app: str) -> bool:
    return which(app) is not None


def prefer(*candidates: str) -> str | None:
    for c in candidates:
        if exists(c):
            return c
    return None


def get_browser() -> str:
    return prefer("firefox", "chromium", "chromium-browser") or "xdg-open"


def get_screenshot_cmd() -> str:
    if exists("scrot"):
        return "scrot ~/Pictures/screenshot_$(date +%Y%m%d_%H%M%S).png"
    if exists("maim"):
        return "maim ~/Pictures/screenshot_$(date +%Y%m%d_%H%M%S).png"
    if exists("flameshot"):
        return "flameshot gui"
    return "import ~/Pictures/screenshot_$(date +%Y%m%d_%H%M%S).png"


def get_audio_player() -> str:
    return prefer("mpv", "mpg123", "mpg321") or "mpv"
