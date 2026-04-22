"""
charclaw/loader.py - Persona loader.

Loads a persona JSON file from the charclaw/ directory and
returns a Persona instance.

To create a new persona:
  1. Copy charclaw/nila.json to charclaw/yourname.json
  2. Edit the fields.
  3. Set CHARCLAW_PERSONA=yourname in your environment,
     or pass --persona yourname on the CLI.
"""

import json
import os

from charclaw.persona import Persona

_PERSONA_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT     = "nila"


def load_persona(name: str | None = None) -> Persona:
    """
    Load a persona by name.
    Falls back to 'nila' if the named file is not found.
    Reads CHARCLAW_PERSONA env variable if name is not supplied.
    """
    if not name:
        name = os.environ.get("CHARCLAW_PERSONA", _DEFAULT)

    path = os.path.join(_PERSONA_DIR, f"{name.lower()}.json")

    if not os.path.exists(path):
        path = os.path.join(_PERSONA_DIR, f"{_DEFAULT}.json")

    with open(path, "r") as f:
        data = json.load(f)

    return Persona(
        name          = data.get("name", "Nila"),
        tone          = data.get("tone", "neutral"),
        verbosity     = data.get("verbosity", "medium"),
        safety        = data.get("safety", "standard"),
        greeting      = data.get("greeting",      "Ready."),
        farewell      = data.get("farewell",       "Goodbye."),
        done_message  = data.get("done_message",   "Done."),
        error_message = data.get("error_message",  "An error occurred."),
        block_message = data.get("block_message",  "This command is blocked."),
        style         = data.get("style", {}),
    )


def list_personas() -> list[str]:
    """Return names of all available persona files."""
    return [
        f[:-5] for f in os.listdir(_PERSONA_DIR)
        if f.endswith(".json") and not f.startswith("_")
    ]
