"""
Charclaw (Beta) - AI Terminal Assistant
main.py - Boot sequence, model selection, and main interaction loop
"""

import os
import sys
import json

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.markup import escape
from rich.rule import Rule

from core.engine      import generate_command
from core.safety      import check_safety
from core.executor    import execute_command
from core.model_picker import pick_model
from charclaw.loader  import load_persona
from memory.store     import remember_command, get_history, kv_set, kv_get, tick_session

console = Console()

CONFIG_FILE = os.path.join(ROOT, "config", "config.json")


# ── config ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {"model": "", "persona": "nila", "voice_enabled": False, "version": "0.1.0-beta"}

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ── banner ────────────────────────────────────────────────────────────────────

BANNER = r"""
  ██████╗██╗  ██╗ █████╗ ██████╗  ██████╗██╗      █████╗ ██╗    ██╗
 ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔════╝██║     ██╔══██╗██║    ██║
 ██║     ███████║███████║██████╔╝██║     ██║     ███████║██║ █╗ ██║
 ██║     ██╔══██║██╔══██║██╔══██╗██║     ██║     ██╔══██║██║███╗██║
 ╚██████╗██║  ██║██║  ██║██║  ██║╚██████╗███████╗██║  ██║╚███╔███╔╝
  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝
"""

def show_banner(version: str = "0.1.0-beta"):
    console.clear()
    console.print()
    t = Text(BANNER)
    t.stylize("bold cyan")
    console.print(t)

    meta = Table.grid(padding=(0, 3))
    meta.add_row(
        "[cyan]AI Terminal Assistant[/cyan]",
        f"[dim]{version}[/dim]",
        "[dim]local · offline · open source[/dim]",
    )
    console.print(meta)
    console.print()
    console.print(Rule(style="dim cyan"))
    console.print()


# ── boot sequence ─────────────────────────────────────────────────────────────

def boot() -> tuple[dict, object]:
    """
    Full boot sequence:
      1. Show banner
      2. Model picker (user selects from ollama list)
      3. Load persona
      4. Return (config, persona)
    """
    config = load_config()

    show_banner(config.get("version", "0.1.0-beta"))

    # model selection every boot
    last_model = config.get("model") or kv_get("last_model", "")
    selected_model = pick_model(current=last_model)

    config["model"] = selected_model
    kv_set("last_model", selected_model)
    save_config(config)

    persona = load_persona(config.get("persona", "nila"))

    tick_session()

    console.print(Rule(style="dim cyan"))
    console.print()
    console.print(f"  [bold cyan]{persona.name}[/bold cyan]  {persona.greeting}")
    console.print()
    console.print(
        "  [dim]Describe a task in plain English. "
        "Type [bold]help[/bold] for commands, [bold]exit[/bold] to quit.[/dim]"
    )
    console.print()

    return config, persona


# ── display helpers ────────────────────────────────────────────────────────────

def display_result(cmd: str, explanation: str, safety):
    color = {"safe": "green", "warn": "yellow", "block": "red"}.get(safety.level, "white")

    g = Table.grid(padding=(0, 2))
    g.add_row("[dim]command    [/dim]", f"[bold yellow]{escape(cmd)}[/bold yellow]")
    g.add_row("[dim]explanation[/dim]", f"[white]{explanation}[/white]")
    g.add_row("[dim]safety     [/dim]", f"[{color}]{safety.label}[/{color}]")
    if safety.reason:
        g.add_row("[dim]reason     [/dim]", f"[dim]{safety.reason}[/dim]")

    console.print()
    console.print(Panel(g, border_style=color, box=box.ROUNDED, padding=(0, 1)))


def show_output(out: str, success: bool):
    out = out.strip()
    if not out or out in ("done", "Done."):
        return
    color = "green" if success else "red"
    icon  = "[green]ok[/green]" if success else "[red]error[/red]"
    if len(out) < 120 and "\n" not in out:
        console.print(f"  {icon}  [dim]{escape(out)}[/dim]")
    else:
        console.print(Panel(
            escape(out[:2000]),
            border_style=color, box=box.SIMPLE_HEAD, padding=(0, 2)
        ))


def confirm(prompt: str) -> bool:
    import termios, tty
    console.print(f"\n  [bold]{prompt}[/bold]  [dim][[green]y[/green]/[red]n[/red]][/dim] ", end="")
    fd  = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    console.print("[green]yes[/green]" if ch == "y" else "[red]no[/red]")
    return ch == "y"


# ── help + history ─────────────────────────────────────────────────────────────

def show_help(model: str, persona_name: str):
    t = Table("input", "action", box=box.SIMPLE_HEAD,
              border_style="cyan", header_style="bold cyan")
    rows = [
        ("describe a task",    "generate and run a shell command"),
        ("history",            "show last 10 commands"),
        ("model",              "re-open model picker"),
        ("help",               "show this message"),
        ("exit / quit",        "quit Charclaw"),
    ]
    for r in rows:
        t.add_row(*r)

    info = Table.grid(padding=(0, 2))
    info.add_row("[dim]active model  [/dim]", f"[cyan]{model}[/cyan]")
    info.add_row("[dim]active persona[/dim]", f"[cyan]{persona_name}[/cyan]")

    console.print(Panel(t,    title="[dim]commands[/dim]", border_style="cyan", box=box.ROUNDED))
    console.print(Panel(info, title="[dim]session[/dim]",  border_style="dim",  box=box.ROUNDED))


def show_history():
    history = get_history(limit=10)
    if not history:
        console.print("  [dim]No history yet.[/dim]")
        return
    t = Table("#", "input", "command", "ok", "time",
              box=box.SIMPLE_HEAD, border_style="cyan", header_style="bold cyan")
    for i, h in enumerate(reversed(history), 1):
        ok = "[green]yes[/green]" if h["success"] else "[red]no[/red]"
        t.add_row(str(i), h["input"][:35], h["command"][:35], ok, h.get("time", ""))
    console.print(Panel(t, title="[dim]history[/dim]", border_style="cyan", box=box.ROUNDED))


# ── main loop ─────────────────────────────────────────────────────────────────

def run():
    try:
        config, persona = boot()
    except KeyboardInterrupt:
        console.print("\n  Aborted.")
        return

    model = config["model"]

    while True:
        console.print("[bold yellow]  > [/bold yellow]", end="")
        try:
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        # ── built-in commands ────────────────────────────────────────────────
        if user_input.lower() in ("exit", "quit", "bye"):
            console.print(f"\n  [bold cyan]{persona.name}[/bold cyan]  {persona.farewell}\n")
            break

        if user_input.lower() == "history":
            show_history()
            continue

        if user_input.lower() in ("help", "?"):
            show_help(model, persona.name)
            continue

        # re-open model picker mid-session
        if user_input.lower() == "model":
            model = pick_model(current=model)
            config["model"] = model
            kv_set("last_model", model)
            save_config(config)
            console.print(f"  Model switched to [cyan]{model}[/cyan]\n")
            continue

        # ── command generation ───────────────────────────────────────────────
        console.print("  [dim]thinking...[/dim]", end="\r")
        result = generate_command(user_input, model=model)
        console.print(" " * 30, end="\r")

        if not result.success:
            console.print(f"\n  [bold cyan]{persona.name}[/bold cyan]  {result.error_message}\n")
            continue

        # ── safety check ─────────────────────────────────────────────────────
        safety = check_safety(result.command)
        display_result(result.command, result.explanation, safety)

        if safety.level == "block":
            console.print(f"\n  [bold cyan]{persona.name}[/bold cyan]  {persona.block_message}\n")
            continue

        # ── confirm + execute ─────────────────────────────────────────────────
        prompt = (
            "Execute?"
            if safety.level == "safe"
            else "This command requires caution. Execute anyway?"
        )

        if confirm(prompt):
            console.print()
            out, success = execute_command(result.command)
            show_output(out, success)
            remember_command(user_input, result.command, success)
            tag = persona.done_message if success else persona.error_message
            console.print(f"\n  [bold cyan]{persona.name}[/bold cyan]  {tag}")
        else:
            console.print(f"\n  [bold cyan]{persona.name}[/bold cyan]  Cancelled.")

        console.print()


if __name__ == "__main__":
    run()
