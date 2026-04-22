"""
core/model_picker.py - Interactive Ollama model selection menu.

Runs once at boot. Lets the user pick from locally available models.
Falls back to a default if Ollama is unreachable or no models exist.
"""

import subprocess
import sys
import re
import termios
import tty

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

_DEFAULT_MODEL = "qwen2.5-coder:1.5b"


# ── fetch installed models ────────────────────────────────────────────────────

def get_ollama_models() -> list[dict]:
    """
    Returns list of dicts: [{name, size, modified}]
    Empty list if Ollama is not running or no models are installed.
    """
    try:
        r = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=6
        )
        if r.returncode != 0:
            return []
        return _parse_ollama_list(r.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def _parse_ollama_list(output: str) -> list[dict]:
    models = []
    lines = output.strip().split("\n")
    # skip header line ("NAME   ID   SIZE   MODIFIED")
    for line in lines[1:]:
        if not line.strip():
            continue
        # capture: name  id  <number unit>  <rest as modified>
        m = re.match(r"(\S+)\s+\S+\s+([\d.]+\s+\w+B)\s+(.*)", line)
        if m:
            models.append({
                "name":     m.group(1),
                "size":     m.group(2),
                "modified": m.group(3).strip(),
            })
        else:
            parts = line.split()
            models.append({"name": parts[0], "size": "?", "modified": "?"})
    return models


# ── single keypress ───────────────────────────────────────────────────────────

def _getch() -> str:
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


# ── menu ──────────────────────────────────────────────────────────────────────

def pick_model(current: str = "") -> str:
    """
    Displays an interactive model picker.
    Returns the selected model name string.

    - If Ollama is unreachable, returns current or default.
    - If only one model exists, auto-selects it (no menu needed).
    - User presses a number key — no Enter required.
    """
    models = get_ollama_models()

    if not models:
        console.print(
            "  [yellow]Ollama not reachable or no models installed.[/yellow]\n"
            f"  Using default: [cyan]{current or _DEFAULT_MODEL}[/cyan]\n"
        )
        return current or _DEFAULT_MODEL

    if len(models) == 1:
        name = models[0]["name"]
        console.print(f"  One model found: [cyan]{name}[/cyan]  — auto-selected.\n")
        return name

    # build table
    t = Table(
        "#", "model", "size", "last modified",
        box=box.SIMPLE_HEAD,
        border_style="cyan",
        header_style="bold cyan",
        padding=(0, 2),
    )
    for i, m in enumerate(models, 1):
        active = " [green]*[/green]" if m["name"] == current else ""
        t.add_row(str(i), f"[white]{m['name']}[/white]{active}", m["size"], m["modified"])

    console.print()
    console.print("  [bold cyan]Select a model[/bold cyan]  [dim](press number key)[/dim]")
    console.print()
    console.print(t)

    # show current if set
    if current:
        console.print(f"  [dim]Current: {current}  — press Enter to keep[/dim]")

    console.print()
    console.print("  [bold yellow]>[/bold yellow] ", end="")

    # read single keypress
    valid = {str(i) for i in range(1, len(models) + 1)}

    while True:
        ch = _getch()
        if ch in ("\r", "\n") and current:
            console.print(f"[dim]keeping {current}[/dim]")
            return current
        if ch in valid:
            selected = models[int(ch) - 1]["name"]
            console.print(f"[cyan]{selected}[/cyan]")
            console.print()
            return selected
        if ch in ("\x03", "\x04"):  # Ctrl+C / Ctrl+D
            raise KeyboardInterrupt
        # ignore other keys silently
