"""
skills/base.py - Base class for all NilaClaw skills.

To add a skill:
  1. Create skills/your_name_skill.py
  2. Define a class that inherits BaseSkill
  3. Implement can_handle() and execute()
  4. NilaClaw auto-discovers it on next launch — no registration needed.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SkillResult:
    success: bool
    output: str          = ""
    steps: list[str]     = field(default_factory=list)
    speak: str           = ""


class BaseSkill(ABC):
    # Override in subclass
    name: str        = "unnamed"
    description: str = ""

    @abstractmethod
    def can_handle(self, intent: dict) -> bool:
        """Return True if this skill should handle the given intent dict."""
        ...

    @abstractmethod
    def execute(self, intent: dict, config: dict) -> SkillResult:
        """Run the skill. Return a SkillResult."""
        ...
