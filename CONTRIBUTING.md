# Contributing to NilaClaw

Thank you for your interest in contributing.

## What to contribute

- Bug fixes
- New persona JSON files in `charclaw/`
- New skill plugins in `skills/`
- Safety rule additions in `core/safety.py`
- Documentation improvements

## Guidelines

- Keep changes focused. One feature or fix per pull request.
- Do not add new dependencies without discussion.
- All new Python files must have a module-level docstring.
- Test your changes locally before submitting.

## Adding a persona

1. Copy `charclaw/nila.json` to `charclaw/yourname.json`
2. Edit the fields — see README for field descriptions
3. Test with `CHARCLAW_PERSONA=yourname python3 main.py`
4. Submit a PR with a brief description of the persona's style

## Adding a skill

1. Create `skills/yourname_skill.py`
2. Subclass `BaseSkill` from `skills.base`
3. Implement `can_handle()` and `execute()`
4. Test locally — skills are auto-discovered on launch

## Reporting issues

Open a GitHub issue with:
- Your OS and Python version
- The command you ran
- The full error output
