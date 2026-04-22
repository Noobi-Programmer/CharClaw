"""
core/executor.py - Shell command execution.

Handles two execution modes:
  - GUI / background apps: Popen (non-blocking, no hang)
  - Terminal commands: subprocess.run with output capture and timeout
"""

import subprocess
import re

# Apps that must be launched in the background
_GUI_APPS = {
    "firefox", "chromium", "chromium-browser", "xdg-open",
    "thunar", "nautilus", "nemo", "pcmanfm",
    "gimp", "inkscape", "vlc", "mpv",
    "gedit", "xed", "mousepad", "kate", "code", "codium",
    "evince", "okular", "eog",
}

_TIMEOUT = 20  # seconds


def execute_command(command: str) -> tuple[str, bool]:
    """
    Execute a shell command.

    Returns:
        (output_string, success_bool)
    """
    first_word = _first_word(command)

    if first_word in _GUI_APPS or command.rstrip().endswith("&"):
        return _launch_background(command, first_word)

    return _run_captured(command)


# ── internal ──────────────────────────────────────────────────────────────────

def _first_word(command: str) -> str:
    parts = command.strip().rstrip("&").strip().split()
    return parts[0].lstrip("./").lower() if parts else ""


def _launch_background(command: str, name: str) -> tuple[str, bool]:
    """Fire-and-forget launch for GUI applications."""
    try:
        subprocess.Popen(
            command, shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return f"Launched {name}.", True
    except Exception as e:
        return str(e), False


def _run_captured(command: str) -> tuple[str, bool]:
    """Run terminal command and capture output."""
    try:
        r = subprocess.run(
            command, shell=True,
            capture_output=True, text=True,
            timeout=_TIMEOUT
        )
        out = (r.stdout or r.stderr or "Done.").strip()
        return out, r.returncode == 0
    except subprocess.TimeoutExpired:
        # If it timed out it is likely a GUI or long-running process — launch it
        subprocess.Popen(command + " &", shell=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Process launched in background (exceeded time limit).", True
    except Exception as e:
        return str(e), False
