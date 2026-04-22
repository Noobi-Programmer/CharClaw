"""
skills/registry.py - Skill auto-discovery and routing.

Scans the skills/ directory for any *_skill.py file and loads
classes that inherit BaseSkill. No manual registration required.
"""

import os
import importlib.util

from skills.base import BaseSkill, SkillResult


class SkillRegistry:
    def __init__(self):
        self._skills: list[BaseSkill] = []

    def load(self, skills_dir: str):
        """Scan a directory and load all *_skill.py files."""
        for fname in sorted(os.listdir(skills_dir)):
            if not fname.endswith("_skill.py"):
                continue
            path = os.path.join(skills_dir, fname)
            spec = importlib.util.spec_from_file_location(fname[:-3], path)
            mod  = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                print(f"[skills] Could not load {fname}: {e}")
                continue
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseSkill)
                    and obj is not BaseSkill
                ):
                    self._skills.append(obj())

    def route(self, intent: dict, config: dict) -> SkillResult | None:
        """Find the first matching skill and execute it."""
        for skill in self._skills:
            try:
                if skill.can_handle(intent):
                    return skill.execute(intent, config)
            except Exception as e:
                return SkillResult(success=False, output=str(e), speak="skill error")
        return None

    def list_skills(self) -> list[str]:
        return [f"{s.name}: {s.description}" for s in self._skills]


# Module-level singleton
registry = SkillRegistry()
