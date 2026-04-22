"""
charclaw/persona.py - Persona data model.

A Persona controls how NilaClaw communicates:
  name       - display name shown in the CLI
  tone       - description of communication style (used in future AI prompts)
  verbosity  - how much output to show ("low" | "medium" | "high")
  safety     - safety strictness ("standard" | "high")
  greeting / farewell / done_message / error_message / block_message
               - fixed response strings for common events
  style      - dict of UI flags (use_emoji, use_panels, confirm_all)
"""

from dataclasses import dataclass, field


@dataclass
class Persona:
    name: str
    tone: str          = "neutral"
    verbosity: str     = "medium"
    safety: str        = "standard"

    greeting: str      = "Ready."
    farewell: str      = "Goodbye."
    done_message: str  = "Done."
    error_message: str = "An error occurred."
    block_message: str = "This command is blocked by the safety policy."

    style: dict        = field(default_factory=lambda: {
        "use_emoji":   False,
        "use_panels":  True,
        "confirm_all": False,
    })

    def __getitem__(self, key: str):
        """Allow dict-style access for compatibility with persona dict usage."""
        return getattr(self, key)

    def get(self, key: str, default=None):
        return getattr(self, key, default)
