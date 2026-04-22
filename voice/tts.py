"""
voice/tts.py - Text-to-speech wrapper using edge-tts.

Features:
  - Interrupts previous playback before starting new
  - Strips rich markup and emoji before speaking
  - Session-level cache for short repeated phrases
  - Non-blocking: all playback runs in daemon threads
  - Silent fail if edge-tts or audio player is not installed
"""

import asyncio
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import threading


# ── configuration ─────────────────────────────────────────────────────────────

_DEFAULT_VOICE = "en-US-AriaNeural"
_CACHE_DIR     = tempfile.mkdtemp(prefix="nilaclaw_tts_")

_enabled = True
_voice   = _DEFAULT_VOICE

# Process control
_current_proc: subprocess.Popen | None = None
_proc_lock = threading.Lock()

# In-session cache: hash → mp3 path
_phrase_cache: dict[str, str] = {}

# Locate edge-tts binary
_TTS_CANDIDATES = [
    os.path.expanduser("~/AI/nliaclawv4/env/bin/edge-tts"),
    os.path.expanduser("~/AI/nilaclaw/env/bin/edge-tts"),
    os.path.expanduser("~/.local/bin/edge-tts"),
]
_TTS_BIN: str | None = next(
    (p for p in _TTS_CANDIDATES if os.path.isfile(p)),
    shutil.which("edge-tts")
)


# ── public API ────────────────────────────────────────────────────────────────

def set_enabled(val: bool):
    global _enabled
    _enabled = val

def is_enabled() -> bool:
    return _enabled

def set_voice(voice: str):
    global _voice
    _voice = voice

def stop():
    """Stop current playback immediately."""
    _kill_current()

def speak(text: str):
    """Speak text. Non-blocking. Interrupts any current playback."""
    if not _enabled:
        return
    clean = _clean(text)
    if not clean:
        return
    threading.Thread(target=_run, args=(clean,), daemon=True).start()


# ── internals ────────────────────────────────────────────────────────────────

_RICH_TAG   = re.compile(r"\[/?[a-zA-Z_ ]+\]")
_NON_ASCII  = re.compile(r"[^\x00-\x7F]+")
_WHITESPACE = re.compile(r"\s+")

def _clean(text: str) -> str:
    text = _RICH_TAG.sub("", text)
    text = _NON_ASCII.sub("", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()


def _kill_current():
    global _current_proc
    with _proc_lock:
        if _current_proc and _current_proc.poll() is None:
            try:
                _current_proc.kill()
            except Exception:
                pass
        _current_proc = None


def _audio_player() -> list[str] | None:
    if shutil.which("mpv"):
        return ["mpv", "--no-terminal", "--really-quiet"]
    if shutil.which("mpg123"):
        return ["mpg123", "-q"]
    if shutil.which("mpg321"):
        return ["mpg321", "-q"]
    return None


def _play(path: str):
    global _current_proc
    player = _audio_player()
    if not player:
        return
    with _proc_lock:
        _current_proc = subprocess.Popen(
            player + [path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    _current_proc.wait()


def _generate(text: str, out_path: str):
    if _TTS_BIN:
        subprocess.run(
            [_TTS_BIN, "--voice", _voice, "--text", text, "--write-media", out_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15
        )
        return
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, _voice).save(out_path))
    except Exception:
        pass


def _run(text: str):
    _kill_current()
    key = hashlib.md5(f"{_voice}:{text}".encode()).hexdigest()

    cached = _phrase_cache.get(key)
    if cached and os.path.exists(cached):
        _play(cached)
        return

    out_path = os.path.join(_CACHE_DIR, f"{key}.mp3")
    _generate(text, out_path)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        if len(text) < 80:
            _phrase_cache[key] = out_path  # cache short phrases
        _play(out_path)
        if len(text) >= 80:
            try:
                os.remove(out_path)
            except Exception:
                pass
