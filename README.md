# AI-Based Voice-Enabled Intelligent System Assistant

An offline, voice-controlled Windows desktop automation system. Speak natural commands to manage files, control applications, send messages, and operate your system — all without cloud connectivity.

---

## The Problem

Existing voice assistants (Siri, Alexa, Google) require constant internet, send your data to the cloud, and can't deeply automate your desktop. Power users need a **private, offline, extensible** voice assistant that actually controls their machine.

## The Solution

A modular, agent-based voice assistant that runs **entirely on your local machine**:

- **Whisper STT** transcribes speech offline (GPU-accelerated)
- **Local LLM** (Ollama) understands intent and generates execution plans
- **17+ automation tools** execute real OS-level actions
- **Piper TTS** speaks results back naturally
- Falls back to keyword matching when LLM is unavailable — always works

---

## Architecture

```
Voice/Text ──► Whisper STT ──► Assistant Controller ──► LLM Client (Ollama / Keyword Fallback)
                                       │
                                       ▼
                                 Execution Plan
                                       │
                                       ▼
                              Multi-Step Executor ──► Tool Registry (17+ tools)
                                       │
                                       ▼
                                 Automation Layer
                          ┌────────┬────────┬──────────┐
                          │ Files  │ System │ Apps     │
                          │ Ops    │ Control│ WhatsApp │
                          │        │ Volume │ Browser  │
                          │        │ Power  │ Email    │
                          └────────┴────────┴──────────┘
                                       │
                                       ▼
                                Piper TTS ──► Voice Response
```

---

## Features

| Category | What You Can Do |
|---|---|
| **File Management** | Create, open, delete, move files & folders; file search; safe Recycle Bin deletion with undo history |
| **System Control** | Volume up/down/mute, lock workstation, shutdown, restart (with confirmation) |
| **WhatsApp** | Open WhatsApp Desktop, send messages to contacts, open specific chats |
| **Browser** | Open URLs, Google search, YouTube — auto-formatted and validated |
| **Applications** | Launch Chrome, Notepad, Calculator, and more |
| **Email** | Send emails via SMTP with validation |
| **Intelligence** | Multi-step planning, confidence scoring (0.0–1.0), parameter extraction & validation |
| **Safety** | Confirmation prompts for dangerous actions, window detection, process verification, error recovery |

### Command Examples

```
"Create file report.txt in Documents"
"Delete folder OldProjects from Desktop"
"Send hello to John on WhatsApp"
"Volume up"
"Lock my laptop"
"Search for budget.xlsx"
"Open youtube"
```

---

## How It Works

1. **Input** — Hold `SPACE` (push-to-talk) or press `CTRL+T` (text mode)
2. **Transcribe** — Whisper converts audio to text
3. **Understand** — LLM generates a structured execution plan (JSON with tool calls + parameters)
4. **Validate** — Parameters are extracted, validated, and scored for confidence
5. **Execute** — Multi-executor runs each step; high-risk actions require voice confirmation
6. **Respond** — Piper TTS speaks the result

### Confidence-Based Execution

Every command is scored `0.0` to `1.0`:

| Score | Action |
|---|---|
| **≥ 0.8** | Auto-execute |
| **0.5 – 0.8** | Ask confirmation |
| **0.3 – 0.5** | Request clarification |
| **< 0.3** | Reject — ask to rephrase |

---

## Project Structure

```
backend/
├── core/                  # Orchestration, parsing, execution, tool registry
├── llm/                   # LLM client, parameter extraction & validation
├── voice_engine/          # Whisper STT, Piper TTS, audio pipeline
├── automation/            # All automation tools (files, system, apps, WhatsApp, email)
├── memory/                # Session state & conversation history
├── config/                # Logger, settings
├── api_service.py         # Flask REST + WebSocket API for desktop UI
└── app.py                 # Minimal CLI entry point
desktop_1/                 # Desktop UI client
tests/                     # 90+ tests with full mocking
app.py                     # Main CLI voice loop
```

---

## Getting Started

### Prerequisites

- **OS:** Windows 10/11
- **Python:** 3.8+
- **GPU:** NVIDIA (optional, speeds up Whisper)
- **Ollama:** Optional — system works without it via keyword fallback

### Installation

```bash
# Clone
git clone https://github.com/your-repo/AI-Voice-Assistant.git
cd AI-Based-Voice-Enabled-Intelligent-System-Assistant

# Virtual environment
python -m venv venv
venv\Scripts\activate

# Dependencies
pip install -r backend/requirements.txt
```

### Install Ollama (Optional)

```bash
# Download from https://ollama.ai, then:
ollama pull qwen2.5:7b-instruct
```

> Without Ollama, the system uses built-in keyword matching — fully functional.

### Configure Email (Optional)

```bash
set SMTP_HOST=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
```

---

## Running

### Mode 1: CLI Voice Loop

```bash
python app.py
```

Hold `SPACE` to talk, `CTRL+T` to type. Say `exit` to quit.

### Mode 2: Desktop UI + API Backend

```bash
# Terminal 1 — Start backend API
python backend/api_service.py

# Terminal 2 — Run desktop client
cd desktop_1
python main.py
```

The API exposes REST endpoints and WebSocket events for real-time communication:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/status` | GET | Assistant status |
| `/api/process_command` | POST | Send a text command |
| `/api/start_listening` | POST | Start voice mode |
| `/api/stop_listening` | POST | Stop voice mode |
| `/api/confirm` | POST | Approve/reject pending action |
| `/api/speak` | POST | Trigger TTS |

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for full reference.

---

## Testing

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html
```

**90+ tests** covering STT, TTS, intent parsing, file operations, tool registry, error handling, command parsing, confidence tracking — all fully mocked, no real side effects.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.8+ |
| STT | OpenAI Whisper (offline, GPU) |
| TTS | Piper TTS (offline) |
| LLM | Ollama (Qwen 2.5 7B) + keyword fallback |
| API | Flask + Flask-SocketIO |
| Automation | pyautogui, keyboard, subprocess |
| Testing | pytest, pytest-cov, pytest-mock |

---

## Future Scope

- **Contextual multi-turn conversations** — maintain deeper dialogue state across commands
- **Plugin system** — allow third-party tool development and hot-loading
- **GUI dashboard** — visual command history, analytics, and system monitoring
- **Cross-platform support** — extend to macOS and Linux
- **Advanced permission model** — role-based access control for shared environments
- **Wake word detection** — hands-free activation without push-to-talk
- **Multilingual support** — extend STT/TTS to other languages

---

## Authors

- **Vansh Raghav** — Voice & Automation Core
- Team Members — LLM Integration, UI & Deployment

---

> **Status:** Production-ready local automation system with scalable agent architecture.
