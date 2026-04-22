"""
core/safety.py - Command safety classification.

Three levels:
  safe  - no known risk, execute after single confirm
  warn  - potentially destructive, confirm with stronger warning
  block - unconditionally refused
"""

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SafetyResult:
    level: str        # "safe" | "warn" | "block"
    label: str        # display string
    reason: str = ""  # why it was flagged


# ── rule definitions ──────────────────────────────────────────────────────────

# (pattern, level, reason)
_RULES: List[Tuple[str, str, str]] = [

    # block: irrecoverable / system-destructive
    (r"rm\s+-[rf]{1,3}\s+/",              "block", "recursive delete at filesystem root"),
    (r"rm\s+-[rf]{1,3}\s+~\s*$",          "block", "recursive delete of home directory"),
    (r"mkfs(\.\w+)?\s+/dev/",             "block", "formats a block device"),
    (r"dd\s+if=.+of=/dev/(?!null)",        "block", "writes directly to a block device"),
    (r":\(\)\s*\{.*\};\s*:",              "block", "fork bomb"),
    (r">\s*/dev/s[db]\w*",                "block", "overwrites a disk device"),
    (r"shred\s+.*/dev/",                  "block", "shreds a block device"),

    # block: privilege escalation + system config
    (r"sudo\s+rm\s+-[rf]",                "block", "privileged recursive delete"),
    (r"sudo\s+chmod\s+777\s+/",           "block", "world-writable on /"),
    (r"sudo\s+passwd\s+root",             "block", "changes root password"),
    (r"visudo",                           "block", "modifies sudo configuration"),

    # warn: potentially destructive but recoverable
    (r"rm\s+",                            "warn",  "deletes files permanently"),
    (r"sudo\s+",                          "warn",  "requires elevated privileges"),
    (r"chmod\s+[0-9]{3,4}",              "warn",  "changes file permissions"),
    (r"chown\s+",                         "warn",  "changes file ownership"),
    (r"kill\s+",                          "warn",  "terminates a process"),
    (r"pkill\s+",                         "warn",  "terminates processes by name"),
    (r"shutdown",                         "warn",  "shuts down the system"),
    (r"reboot",                           "warn",  "restarts the system"),
    (r"systemctl\s+(stop|disable|mask)",  "warn",  "stops or disables a system service"),
    (r"apt(-get)?\s+(remove|purge)",      "warn",  "uninstalls packages"),
    (r">\s+[^\s]",                        "warn",  "overwrites a file with redirection"),
    (r"mv\s+.+\s+/",                      "warn",  "moves files to a system directory"),
]


# ── public API ────────────────────────────────────────────────────────────────

def check_safety(command: str) -> SafetyResult:
    """
    Returns SafetyResult for a given shell command string.
    Rules are evaluated in order; first match wins.
    """
    for pattern, level, reason in _RULES:
        if re.search(pattern, command, re.IGNORECASE):
            labels = {
                "block": "BLOCKED — will not execute",
                "warn":  "Caution — review before running",
            }
            return SafetyResult(level=level, label=labels[level], reason=reason)

    return SafetyResult(level="safe", label="Safe to run")
