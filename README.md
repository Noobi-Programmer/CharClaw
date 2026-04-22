# Charclaw — AI Terminal Assistant

![Status](https://img.shields.io/badge/status-beta-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)
![Ollama](https://img.shields.io/badge/powered%20by-Ollama-black)

<p align="center">
  <img src="assets/charclaw_logo2.png" alt="CharClaw Logo" width="500"/>
</p>

<h1 align="center">NilaClaw</h1>
<p align="center"><b>AI Terminal Assistant with Character Personas</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/status-beta-orange">
  <img src="https://img.shields.io/badge/python-3.10+-blue">
  <img src="https://img.shields.io/badge/license-MIT-green">
</p>

**Charclaw** is a local AI terminal assistant. Describe a task in plain English — Charclaw generates the shell command, explains it, checks it for safety, and executes it after your confirmation.

Runs entirely on your machine via [Ollama](https://ollama.com). No API keys. No internet required. No data leaves your system.

---

## Status

This is a **Beta** release. Core functionality is working.

| Component         | Status              |
|-------------------|---------------------|
| Command generation | Functional (Beta)  |
| Safety filter     | Functional (Beta)   |
| Model picker      | Functional (Beta)   |
| TTS voice output  | Complete            |
| 3D VRM avatar     | In development      |

> **3D Avatar Note:** A 3D avatar system using the `.vrm` format is currently in active development. Once the VRM avatar layer is stable and integrated, the project will move beyond the Beta label and adopt a new versioning scheme. The current release ships without the avatar — voice output via `edge-tts` is the only audio-visual layer available at this time.

---

## Features

- **Model picker at boot** — select from any model installed in Ollama each time you launch
- **Natural language to shell command** — describe what you want in plain English
- **Command explanation** — see what the command does before it runs
- **Three-tier safety filter** — safe, caution, or blocked
- **Single-keypress confirmation** — no Enter required
- **CharClaw persona system** — swappable personality layer (default: Nila)
- **Voice output** — TTS via `edge-tts` (optional, toggle in config)
- **Persistent command history** — stored locally as JSON
- **Skill plugin system** — drop a `*_skill.py` file to extend functionality
- **Offline-first** — designed for low-end hardware, no GPU required

---

## Architecture

```
charclaw/
├── main.py                 Boot sequence, model picker, CLI loop
│
├── core/
│   ├── engine.py           NL → command generation (Ollama, few-shot)
│   ├── model_picker.py     Interactive Ollama model selection at boot
│   ├── safety.py           Command classification: safe / warn / block
│   ├── executor.py         Execution: GUI-aware (Popen vs subprocess.run)
│   └── sysinfo.py          Installed app detection, cached at startup
│
├── charclaw/
│   ├── persona.py          Persona dataclass
│   ├── nila.json           Default persona definition
│   └── loader.py           JSON loader, env var override support
│
├── skills/
│   ├── base.py             BaseSkill abstract class + SkillResult
│   └── registry.py         Auto-discovery, no registration required
│
├── voice/
│   └── tts.py              edge-tts wrapper — interrupt-capable, session-cached
│
├── memory/
│   └── store.py            JSON command history, key-value store
│
└── config/
    └── config.json         User configuration
```

---

## Requirements

- Python 3.10 or later
- [Ollama](https://ollama.com) installed and running
- At least one model pulled (e.g. `ollama pull qwen2.5-coder:1.5b`)

Optional (for voice output):
- `edge-tts`: `pip install edge-tts`
- Audio player: `sudo apt install mpg123` or `sudo apt install mpv`

---

## Installation

```bash
git clone https://github.com/yourusername/charclaw.git
cd charclaw

python3 -m venv env
source env/bin/activate

pip install -r requirements.txt

# pull at least one model
ollama pull qwen2.5-coder:1.5b
```

---

## Usage

```bash
python3 main.py
```

On launch, Charclaw shows all models currently installed in Ollama and asks you to choose one. Press the number key — no Enter needed.

```
  Select a model  (press number key)

  #   model                    size    last modified
  1   qwen2.5-coder:1.5b       986 MB  2 weeks ago
  2   mistral:7b               4.1 GB  3 days ago
  3   llama3.2:3b              2.0 GB  1 week ago

  >
```

Then describe what you want:

```
  > list all files modified today
  > show disk usage
  > find python files larger than 100KB
  > open youtube
```

Charclaw displays the command, explains it, shows its safety classification, and asks for confirmation before running.

**Session commands:**

| Input     | Action                                |
|-----------|---------------------------------------|
| `model`   | Re-open model picker mid-session      |
| `history` | Show last 10 commands                 |
| `help`    | Show help and current session info    |
| `exit`    | Quit                                  |

---

## CharClaw — Persona System

CharClaw is the persona layer. It controls tone, response messages, and style. The default persona is **Nila** (calm, precise, slightly playful).

### Switching personas

```bash
CHARCLAW_PERSONA=nila python3 main.py
```

### Creating a persona

Create a file in `charclaw/yourname.json`:

```json
{
  "name": "Rex",
  "tone": "direct, terse, no-nonsense",
  "verbosity": "low",
  "safety": "standard",

  "greeting":      "Online.",
  "farewell":      "Terminated.",
  "done_message":  "Complete.",
  "error_message": "Failed.",
  "block_message": "Blocked.",

  "style": {
    "use_emoji":   false,
    "use_panels":  false,
    "confirm_all": false
  }
}
```

Launch with `CHARCLAW_PERSONA=rex python3 main.py`.

---

## Safety Model

Every command is classified before execution:

| Level    | Meaning                                         | Action                          |
|----------|-------------------------------------------------|---------------------------------|
| `safe`   | No known destructive patterns                  | Single confirmation, then run   |
| `warn`   | Potentially destructive (rm, sudo, kill, etc.) | Stronger confirmation message   |
| `block`  | Irrecoverable or system-destructive            | Refused, never executed         |

**Permanently blocked patterns:**

- `rm -rf /` and `rm -rf ~`
- `mkfs` on any block device
- `dd` writing to block devices
- Fork bombs (`:(){ :|:&};:`)
- `sudo rm -rf` on system paths

Safety rules live in `core/safety.py` and are plain regex — easy to audit and extend.

---

## Voice Output

TTS is implemented using `edge-tts` (Microsoft Edge neural voices, free, offline-capable). It is **disabled by default**.

To enable, set `"voice_enabled": true` in `config/config.json`.

Voice output is the only audio-visual feature currently implemented. The 3D avatar system is in development — see roadmap below.

---

## Adding Skills

Drop a `*_skill.py` file into `skills/`. It will be auto-discovered on next launch.

```python
from skills.base import BaseSkill, SkillResult

class MySkill(BaseSkill):
    name        = "my_skill"
    description = "Does something custom"

    def can_handle(self, intent: dict) -> bool:
        return intent.get("skill") == "my_skill"

    def execute(self, intent: dict, config: dict) -> SkillResult:
        return SkillResult(success=True, output="result", steps=["Step 1"])
```

---

## Roadmap

### Near-term (Beta)
- [ ] `--dry-run` flag — show command without executing
- [ ] Multi-step task planning (chain of commands)
- [ ] Skill: PDF operations
- [ ] Skill: image conversion and resizing
- [ ] `--persona` and `--model` CLI flags
- [ ] Shell history import

### In development
- [ ] **3D VRM avatar** — a companion avatar using the `.vrm` open format, rendered in a lightweight desktop window. This is the primary visual feature planned for the post-beta release. When complete, Charclaw will render a 3D character that reacts to responses and speaks in sync with TTS output.

### Community
- [ ] Additional persona files
- [ ] Windows and macOS support

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

The easiest contributions:
- New persona JSON files in `charclaw/`
- New skill plugins in `skills/`
- Bug reports with full error output

---

## License

MIT — see [LICENSE](LICENSE).

---

*Charclaw runs entirely on your machine. No commands, inputs, or outputs are sent to any external service.*
