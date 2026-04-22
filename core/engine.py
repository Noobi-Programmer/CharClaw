"""
core/engine.py - Command generation engine.

Converts natural language into a shell command + plain-English explanation.
Model is passed in at call time — selected by the user at boot via model_picker.
"""

import re
import subprocess
from dataclasses import dataclass

from core.sysinfo import get_browser, get_screenshot_cmd


@dataclass
class CommandResult:
    command:       str  = ""
    explanation:   str  = ""
    success:       bool = False
    error_message: str  = ""


# ── constants ─────────────────────────────────────────────────────────────────

_BLOCKLIST = {
    "bash", "sh", "zsh", "fish", "dash",
    "python", "python3", "python2",
    "node", "nodejs", "ruby", "perl",
    "vim", "vi", "nano", "emacs", "nvim",
    "htop", "top", "less", "more", "man",
}

_URL_MAP = {
    r"youtube|open yt\b|open youtube": "youtube.com",
    r"github\b":                       "github.com",
    r"gmail\b":                        "mail.google.com",
    r"\bgoogle\b":                     "google.com",
    r"stackoverflow\b":                "stackoverflow.com",
    r"chatgpt\b":                      "chat.openai.com",
    r"gemini\b":                       "gemini.google.com",
    r"reddit\b":                       "reddit.com",
    r"discord\b":                      "discord.com",
    r"leetcode\b":                     "leetcode.com",
    r"notion\b":                       "notion.so",
}

_GUI_APPS = {
    "firefox", "chromium", "chromium-browser", "xdg-open",
    "thunar", "nautilus", "nemo", "pcmanfm",
    "gimp", "inkscape", "vlc", "mpv",
    "gedit", "xed", "mousepad", "kate", "code", "codium",
    "evince", "okular", "eog",
}

_PROMPT = """\
You are a Linux command generator. Output exactly two lines:
Line 1: the raw terminal command (no backticks, no explanation)
Line 2: one-sentence plain-English explanation of what it does

Examples:

Input: list all files including hidden
Output:
ls -la
Lists all files and directories including hidden ones with full details.

Input: show disk usage
Output:
df -h
Shows disk usage for all mounted filesystems in human-readable units.

Input: find files larger than 100MB
Output:
find ~ -type f -size +100M 2>/dev/null
Searches home directory for files larger than 100 megabytes.

Input: take a screenshot
Output:
{screenshot}
Takes a screenshot and saves it to the Pictures folder.

Input: check memory usage
Output:
free -h
Shows total, used, and available RAM in human-readable format.

Input: {task}
Output:
"""


# ── helpers ───────────────────────────────────────────────────────────────────

def _clean_line(line: str) -> str:
    line = re.sub(r"^```\w*\s*|```$", "", line).strip()
    line = re.sub(r"^\$\s+", "", line).strip()
    line = re.sub(r"^(Output:|Command:|>)\s*", "", line, flags=re.IGNORECASE).strip()
    return line


def _is_valid(cmd: str) -> bool:
    if not cmd or len(cmd) < 2:
        return False
    first = cmd.split()[0].lower().lstrip("./")
    if first in _BLOCKLIST:
        return False
    if re.match(r"^[A-Z][a-z]+\s+[a-z]", cmd) and not re.search(r"[/=|&><~\-]", cmd):
        return False
    return True


def _ensure_background(cmd: str) -> str:
    first = cmd.strip().split()[0].lstrip("./").lower()
    if first in _GUI_APPS and not cmd.rstrip().endswith("&"):
        return cmd.rstrip() + " &"
    return cmd


def _url_shortcut(text: str) -> CommandResult | None:
    t = text.lower()
    for pattern, domain in _URL_MAP.items():
        if re.search(pattern, t):
            browser = get_browser()
            return CommandResult(
                command=f"{browser} https://{domain}",
                explanation=f"Opens {domain} in your browser.",
                success=True,
            )
    return None


def _call_ollama(prompt: str, model: str) -> str:
    try:
        r = subprocess.run(
            ["ollama", "run", model, "--", prompt],
            capture_output=True, text=True, timeout=25
        )
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return ""


def _parse(raw: str) -> tuple[str, str]:
    lines = [_clean_line(l) for l in raw.strip().split("\n") if l.strip()]
    cmd  = lines[0] if lines else ""
    expl = lines[1] if len(lines) > 1 else "No explanation available."
    return cmd, expl


# ── public API ────────────────────────────────────────────────────────────────

def generate_command(user_input: str, model: str) -> CommandResult:
    """
    Generate a shell command for user_input using the given Ollama model.

    Priority:
      1. URL shortcuts (instant, no AI)
      2. Ollama few-shot prompt, up to 3 retries
      3. Failure result
    """
    shortcut = _url_shortcut(user_input)
    if shortcut:
        return shortcut

    screenshot = get_screenshot_cmd()
    prompt = _PROMPT.format(task=user_input, screenshot=screenshot)

    for attempt in range(3):
        raw = _call_ollama(prompt, model)
        if not raw:
            break
        cmd, expl = _parse(raw)
        if _is_valid(cmd):
            return CommandResult(command=_ensure_background(cmd), explanation=expl, success=True)
        prompt = (
            f"Linux terminal command for: {user_input}\n"
            "Line 1: command only. Line 2: one-sentence explanation."
        )

    return CommandResult(
        success=False,
        error_message=(
            "Could not generate a valid command. "
            "Try rephrasing, or be more specific."
        )
    )
