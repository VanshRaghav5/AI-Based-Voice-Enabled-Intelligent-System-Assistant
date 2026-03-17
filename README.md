# AI-Based Voice-Enabled Intelligent System Assistant

An offline, voice-controlled Windows desktop automation system. Speak natural commands to manage files, control applications, send messages, and operate your system — all without cloud connectivity.

---

## The Problem

Existing voice assistants (Siri, Alexa, Google) require constant internet, send your data to the cloud, and can't deeply automate your desktop. Power users need a **private, offline, extensible** voice assistant that actually controls their machine.

## The Solution

A modular, agent-based voice assistant that runs **entirely on your local machine**:

- **Whisper STT** transcribes speech offline (GPU-accelerated)
- **Local LLM** (Ollama) understands intent and drives a bounded agent loop
- **17+ automation tools** execute real OS-level actions
- **Piper TTS** speaks results back naturally
- JWT-authenticated desktop client with login/registration
- Falls back to keyword matching when LLM is unavailable — always works
- **Persistent memory** stores execution context and saved facts across restarts

---

## Architecture

```
                          ┌──────────────────────────┐
                          │    Desktop Client (CTk)   │
                          │  Login → Chat → Voice UI  │
                          └────────┬─────────────────┘
                                   │ REST + Socket.IO
                          ┌────────▼─────────────────┐
                          │   Flask API + WebSocket    │
                          │  JWT Auth │ Rate Limiting  │
                          └────────┬─────────────────┘
                                   │
               ┌───────────────────┼───────────────────┐
               ▼                   ▼                   ▼
        Whisper STT         LLM Client           Piper TTS
        (offline)        (Ollama / Fallback)      (offline)
                               │
                         Execution Plan
                               │
                    Multi-Step Executor
                               │
              ┌────────┬───────┴───────┬────────┐
              │ Files  │  System       │  Apps   │
              │ CRUD   │  Vol/Power    │  Launch │
              │ Search │  Screenshot   │  URLs   │
              │        │  Clipboard    │  Email  │
              └────────┴───────────────┴────────┘
```

---

## Features

| Category | Capabilities |
|----------|-------------|
| **Authentication** | JWT login/register, bcrypt password hashing, token persistence, role-based access |
| **File Management** | Create, open, delete, move files & folders; search; safe Recycle Bin with undo |
| **System Control** | Volume, lock, shutdown, restart (with confirmation), screenshot, clipboard |
| **WhatsApp** | Open desktop app, send messages, open specific chats |
| **Browser** | Open URLs, Google search, YouTube — auto-formatted and validated |
| **Applications** | Launch Chrome, Notepad, Calculator, and more |
| **Email** | Send via SMTP with validation |
| **Intelligence** | Multi-step planning, confidence scoring (0.0–1.0), parameter extraction & validation |
| **Safety** | Confirmation prompts for dangerous actions, window detection, error recovery |
| **Memory** | Persistent state in `backend/data/session_memory.json`, remembered facts (`remember/recall/forget/list`) |
| **Settings** | Theme, persona, language, memory toggle — persisted locally |

### Command Examples

```
"Create file report.txt in Documents"
"Delete folder OldProjects from Desktop"
"Send hello to John on WhatsApp"
"Volume up"
"Lock my laptop"
"Search for budget.xlsx"
"Open youtube"
"Remember that manager name is Priya"
"Recall manager name"
```

### Persistent Memory Quick Use

The assistant now stores memory on disk and reloads it on startup.

- Memory file: `backend/data/session_memory.json`
- Remember: `Remember that wifi password hint is bluecar`
- Recall: `Recall wifi password hint`
- Forget: `Forget wifi password hint`
- List: `List memory`

---

## How It Works

1. **Authenticate** — Login or register via the desktop client
2. **Input** — Type a command or click the mic button for voice
3. **Transcribe** — Whisper converts audio to text (offline)
4. **Understand & Plan** — LLM generates a structured execution plan (JSON with tool calls + parameters)
5. **Agent Loop** — Controller runs `plan -> act -> observe -> replan` (bounded retries)
6. **Execute Safely** — Multi-executor runs each step; high-risk actions require confirmation and exact-step resume
7. **Respond** — Piper TTS speaks the result; chat UI shows message bubbles

### Confidence-Based Execution

Every command is scored `0.0` to `1.0`:

| Score | Action |
|-------|--------|
| **≥ 0.8** | Auto-execute |
| **0.5 – 0.8** | Ask confirmation |
| **0.3 – 0.5** | Request clarification |
| **< 0.3** | Reject — ask to rephrase |

---

## Project Structure

```
AI-Based-Voice-Enabled-Intelligent-System-Assistant/
├── README.md
├── SECURITY_SETUP_GUIDE.md
├── STRUCTURE.md
├── START.bat                      # One-click launcher
├── launcher.bat                   # Debug launcher with logs
├── pytest.ini
├── requirements-test.txt
│
├── backend/                       # Core backend
│   ├── api_service.py             # Flask REST + WebSocket API (entry point)
│   ├── requirements.txt
│   │
│   ├── auth/                      # Authentication
│   │   └── auth_service.py        # JWT token generation, validation, bcrypt
│   │
│   ├── middleware/                 # Request middleware
│   │   ├── auth_middleware.py      # JWT route protection
│   │   └── validation.py          # Marshmallow input schemas
│   │
│   ├── database/                  # Persistence
│   │   └── models.py              # SQLAlchemy User model
│   │
│   ├── agents/                    # AI agents
│   │   ├── intent_agent.py        # Intent classification
│   │   ├── planner_agent.py       # Execution planning
│   │   ├── safety_agent.py        # Risk assessment
│   │   └── tool_agent.py          # Tool selection
│   │
│   ├── automation/                # Automation tools
│   │   ├── app_launcher.py        # Application launching
│   │   ├── browser_control.py     # URL/search/YouTube
│   │   ├── whatsapp_desktop.py    # WhatsApp messaging
│   │   ├── email_tool.py          # SMTP email
│   │   ├── system_control.py      # Volume, lock, power
│   │   ├── file_manager.py        # File CRUD operations
│   │   ├── window_detection.py    # Window state detection
│   │   ├── error_handler.py       # Error recovery
│   │   ├── system/                # Volume, power, screenshot, clipboard, etc.
│   │   └── file/                  # File ops, search, folder ops, delete history
│   │
│   ├── core/                      # Orchestration
│   │   ├── assistant_controller.py# Main controller
│   │   ├── command_parser.py      # NLP command parsing
│   │   ├── tool_registry.py       # Tool discovery & dispatch
│   │   ├── multi_executor.py      # Multi-step execution
│   │   ├── confidence_tracker.py  # Confidence scoring
│   │   └── execution_plan.py      # Plan data structures
│   │
│   ├── llm/                       # Language model
│   │   ├── llm_client.py          # Ollama client + keyword fallback
│   │   ├── parameter_extractor.py # Parameter extraction
│   │   └── parameter_validator.py # Parameter validation
│   │
│   ├── voice_engine/              # Speech I/O
│   │   ├── audio_pipeline.py      # Audio processing pipeline
│   │   ├── stt/                   # Whisper speech-to-text
│   │   └── tts/                   # Piper text-to-speech
│   │
│   ├── memory/                    # State + persistent memory
│   │   ├── memory_store.py        # Thread-safe memory operations
│   │   ├── session_state.py       # Persistent session memory loader/saver
│   │   └── state_schema.py        # State data models
│   │
│   └── config/                    # Configuration
│       ├── assistant_config.py    # Assistant settings
│       ├── assistant_config.json  # Config file
│       ├── settings.py            # App settings
│       └── logger.py              # Logging setup
│
├── desktop/                       # Desktop UI (CustomTkinter)
│   ├── main.py                    # App controller — auth flow, window lifecycle
│   ├── app.py                     # Bootstrap and application wiring
│   ├── config.py                  # UI/client configuration
│   ├── requirements.txt
│   ├── core/                      # Desktop orchestration components
│   ├── services/
│   │   └── api_client.py          # REST client — auth, commands, settings
│   ├── themes/
│   └── ui/                        # Chat, login, visualization, and dialogs
│
├── cli/                           # Command-line interfaces
│   ├── app.py                     # Full CLI voice loop with confirmation
│   └── test.py                    # Simple test CLI
│
├── tests/                         # 90+ unit tests (fully mocked)
├── docs/                          # Documentation
│   ├── README.md                  # Docs index (consolidated)
│   ├── HANDBOOK.md                # Primary operational guide
│   ├── API_DOCUMENTATION.md
│   ├── reports/
│   │   └── REPORTS_SUMMARY.md     # Consolidated report index
│   └── archive/                   # Legacy docs and reports
└── examples/                      # Example code & usage patterns
```

---

## Getting Started

### Prerequisites

- **OS:** Windows 10/11
- **Python:** 3.10+ (3.12 recommended)
- **GPU:** NVIDIA (optional, speeds up Whisper)
- **Ollama:** Optional — system works without it via keyword fallback

### Installation

```bash
# 1. Clone
git clone https://github.com/your-repo/AI-Voice-Assistant.git
cd AI-Based-Voice-Enabled-Intelligent-System-Assistant

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt
pip install -r desktop/requirements.txt

# 4. (Optional) Install Ollama for LLM-powered understanding
# Download from https://ollama.ai, then:
ollama pull qwen2.5:7b-instruct-q4_0
```

### Required Security Environment Variables

Set these once before running the backend (or `START.bat`):

```powershell
setx OMNIASSIST_FLASK_SECRET_KEY "replace-with-long-random-secret"
setx OMNIASSIST_JWT_SECRET "replace-with-long-random-secret"
```

Optional (first-run admin bootstrap):

```powershell
setx OMNIASSIST_BOOTSTRAP_ADMIN_USERNAME "admin"
setx OMNIASSIST_BOOTSTRAP_ADMIN_EMAIL "admin@example.com"
setx OMNIASSIST_BOOTSTRAP_ADMIN_PASSWORD "StrongPassword123!"
```

Optional (restrict CORS origins):

```powershell
setx OMNIASSIST_CORS_ALLOWED_ORIGINS "http://127.0.0.1:5000,http://localhost:5000"
```

> After `setx`, close and reopen terminal/VS Code so variables are available.
> Without Ollama, the system uses built-in keyword matching — fully functional but less intelligent.

### Launch

**One-click (recommended):**
```bash
START.bat
```

**Debug mode (shows logs):**
```bash
launcher.bat
```

**Manual:**
```bash
# Terminal 1 — Backend
python backend/api_service.py

# Terminal 2 — Desktop UI
python desktop/main.py
```

---

## API Reference

### Authentication

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register` | POST | Create account |
| `/api/auth/login` | POST | Authenticate, receive JWT |
| `/api/auth/logout` | POST | Invalidate session |
| `/api/auth/verify` | GET | Validate stored token |

### Assistant

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/process_command` | POST | Execute a text command |
| `/api/start_listening` | POST | Start voice capture |
| `/api/stop_listening` | POST | Stop voice capture |
| `/api/confirm` | POST | Approve/reject pending action |
| `/api/speak` | POST | Text-to-speech output |
| `/api/settings` | GET/POST | Read/update settings |
| `/api/status` | GET | Assistant status |
| `/api/health` | GET | Health check |

### Socket.IO Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `voice_input` | Server → Client | Live speech transcription |
| `command_result` | Server → Client | Execution result |
| `execution_step` | Server → Client | Multi-step progress |
| `confirmation_required` | Server → Client | Safety confirmation |
| `listening_status` | Server → Client | Mic state change |
| `error` | Server → Client | Error notification |
| `send_command` | Client → Server | Submit command via socket |

See [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for full reference.

---

## Security

| Layer | Implementation |
|-------|---------------|
| **Authentication** | JWT tokens (PyJWT + Flask-JWT-Extended) |
| **Password Hashing** | bcrypt with salt rounds |
| **Input Validation** | Marshmallow schemas with field-level validators |
| **SQL Injection** | SQLAlchemy ORM (parameterized queries) |
| **Rate Limiting** | Flask-Limiter on auth endpoints |
| **Token Storage** | Local file (`~/.omniassist/token.json`) |

See [docs/HANDBOOK.md](docs/HANDBOOK.md) and archived security details in [docs/archive/legacy-docs/SECURITY_IMPLEMENTATION.md](docs/archive/legacy-docs/SECURITY_IMPLEMENTATION.md).

---

## Testing

```bash
pip install -r requirements-test.txt
pytest                                    # Run all tests
pytest --cov=backend --cov-report=html    # With coverage report
```

**90+ tests** covering STT, TTS, intent parsing, file operations, tool registry, error handling, command parsing, confidence tracking — all fully mocked, no real side effects.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| STT | OpenAI Whisper (offline, GPU-accelerated) |
| TTS | Piper TTS (offline) |
| LLM | Ollama (Qwen 2.5 7B) + keyword fallback |
| API | Flask + Flask-SocketIO |
| Auth | PyJWT, bcrypt, Flask-JWT-Extended |
| Database | SQLAlchemy (SQLite) |
| Validation | Marshmallow, Pydantic |
| Desktop UI | CustomTkinter |
| Automation | pyautogui, keyboard, subprocess |
| Testing | pytest, pytest-cov, pytest-mock |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend won't start | Check `logs/backend.log` or run `python backend/api_service.py` directly |
| Ollama not responding | Run `ollama serve`, verify with `curl http://localhost:11434/api/tags` |
| UI won't connect | Ensure backend is running; check `http://localhost:5000/api/health` |
| Login window not appearing | Backend must be running before launching desktop client |
| Dependencies missing | `pip install -r backend/requirements.txt -r desktop/requirements.txt` |
| Connection timeout | Increase `timeout_seconds` in `backend/config/assistant_config.json` |

---

## Future Scope

- Contextual multi-turn conversations
- Plugin system for third-party tools
- Visual dashboard with command history and analytics
- Cross-platform support (macOS, Linux)
- Wake word detection for hands-free activation
- Multilingual STT/TTS support

---

## Authors

- **Vansh Raghav** — Voice & Automation Core
- Team Members — LLM Integration, UI & Deployment
