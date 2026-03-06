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
AI-Based-Voice-Enabled-Intelligent-System-Assistant/
├── README.md                  # Main documentation (you are here)
├── START.bat                  # Simple one-click launcher
├── launcher.bat               # Debug launcher with logs
├── pytest.ini                 # Test configuration
├── requirements-test.txt      # Testing dependencies
│
├── backend/                   # Core backend system
│   ├── api_service.py        # Flask REST + WebSocket API (main entry)
│   ├── requirements.txt      # Backend dependencies
│   ├── agents/               # Intent, planner, safety, tool agents
│   ├── automation/           # All automation tools (49 tools)
│   │   ├── app_launcher.py
│   │   ├── browser_control.py
│   │   ├── whatsapp_desktop.py
│   │   ├── email_tool.py
│   │   ├── system/           # Volume, power, screenshot, clipboard, etc.
│   │   └── file/             # File operations, search
│   ├── config/               # Logger, settings, assistant config
│   ├── core/                 # Orchestration, parsing, execution, tool registry
│   ├── llm/                  # LLM client, parameter extraction & validation
│   ├── voice_engine/         # Whisper STT, Piper TTS, audio pipeline
│   ├── memory/               # Session state & conversation history
│   └── data/                 # Runtime data, audio files
│
├── desktop_1/                 # Desktop UI (CustomTkinter)
│   ├── main.py               # UI entry point
│   ├── requirements.txt      # Desktop dependencies
│   ├── ui/                   # Chat window, overlays, visualizers
│   └── services/             # API client, socket client
│
├── cli/                       # Command-line interfaces
│   ├── app.py                # Full CLI voice loop with confirmation
│   └── test.py               # Simple test CLI
│
├── docs/                      # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── SYSTEM_CAPABILITIES.md
│   ├── COMMAND_PARSING_SUMMARY.md
│   ├── CONFIDENCE_SYSTEM_SUMMARY.md
│   ├── TESTING_SUMMARY.md
│   ├── COMPLETE_INSTALLATION_GUIDE.md
│   └── reports/              # Development reports
│       ├── AUTOMATION_STATUS_REPORT.md
│       ├── AUTOMATION_TEST_REPORT.md
│       ├── COMPLETE_FIX_REPORT.md
│       └── LLM_FIX_REPORT.md
│
├── examples/                  # Example code & usage patterns
├── tests/                     # 90+ unit tests (fully mocked)
├── logs/                      # Runtime logs (auto-created)
└── venv/                      # Python virtual environment
```

---

## Getting Started

### Quick Start (Recommended)

**For regular users:**
```bash
# Just double-click:
START.bat
```

**For developers/debugging:**
```bash
# Shows detailed logs:
launcher.bat
```

### Prerequisites

- **OS:** Windows 10/11
- **Python:** 3.8+
- **GPU:** NVIDIA (optional, speeds up Whisper)
- **Ollama:** Optional — system works without it via keyword fallback

### First Time Installation

#### 1. Clone Repository
```bash
git clone https://github.com/your-repo/AI-Voice-Assistant.git
cd AI-Based-Voice-Enabled-Intelligent-System-Assistant
```

#### 2. Setup Python Environment
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r backend/requirements.txt
pip install -r desktop_1/requirements.txt
```

#### 3. Install Ollama (Recommended)
```bash
# Download from https://ollama.ai, then:
ollama pull qwen2.5:7b-instruct-q4_0
```

> **Note:** Without Ollama, the system uses built-in keyword matching — fully functional but less intelligent.

#### 4. Configure Email (Optional)
```bash
set SMTP_HOST=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=your-email@gmail.com
set SMTP_PASSWORD=your-app-password
```

#### 5. Launch
```bash
# Simple launcher (recommended)
START.bat

# Or debug mode with logs
launcher.bat
```

---

## Running

### Mode 1: Desktop UI (Recommended)

**Simple Launch:**
```bash
START.bat
```
- Starts backend API automatically
- Opens desktop UI
- Runs in background
- Best for regular use

**Debug Launch:**
```bash
launcher.bat
```
- Shows detailed logs
- Checks Ollama status
- Displays errors
- Keeps console open
- Best for troubleshooting

### Mode 2: Manual CLI Voice Loop

```bash
python cli/app.py
```

Hold `SPACE` to talk, `CTRL+T` to type. Say `exit` to quit.

### Mode 3: Backend API Only

```bash
python backend/api_service.py
```

The API exposes REST endpoints and WebSocket events for real-time communication:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/status` | GET | Assistant status |
| `/api/process_command` | POST | Send a text command |
| `/api/start_listening` | POST | Start voice mode |
| `/api/stop_listening` | POST | Stop voice mode |
| `/api/confirm` | POST | Approve/reject pending action |
| `/api/health` | GET | Backend health check |

See [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for full reference.

---

## Troubleshooting

### Backend Won't Start
```powershell
# Check logs
type logs\backend.log

# Manual start to see errors
.\venv\Scripts\python.exe backend\api_service.py
```

### Ollama Not Running
```powershell
# Start Ollama server
ollama serve

# In another terminal, verify it's running
ollama ps

# Test API
curl http://localhost:11434/api/tags
```

### Dependencies Missing
```powershell
# Reinstall backend dependencies
.\venv\Scripts\pip install -r backend\requirements.txt

# Reinstall desktop dependencies
.\venv\Scripts\pip install -r desktop_1\requirements.txt
```

### Connection Timeout
```powershell
# Increase timeout in backend/config/assistant_config.json
{
  "llm": {
    "timeout_seconds": 30
  }
}
```

### UI Won't Connect
- Ensure backend is running first
- Check `http://localhost:5000/api/health` in browser
- Verify firewall isn't blocking port 5000

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
