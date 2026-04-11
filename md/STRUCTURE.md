# Project Structure Reference

Quick reference for navigating the codebase. Run `START.bat` to launch the full system.

---

## Directory Layout

```
AI-Based-Voice-Enabled-Intelligent-System-Assistant/
│
├── 📄 Root Files
│   ├── README.md               # Main documentation & setup guide
│   ├── STRUCTURE.md            # This file — project map
│   ├── START.bat               # One-click launcher (start here)
│   ├── launcher.bat            # Debug launcher (shows detailed logs)
│   ├── setup_email.ps1         # SMTP email configuration helper
│   ├── pytest.ini              # Test runner configuration
│   ├── requirements-test.txt   # Test dependencies
│   ├── .gitignore              # Ignored files (venv, logs, runtime data)
│   └── .gitattributes          # Git line-ending settings
│
├── 🔧 backend/                 ← Flask API + all automation logic
│   ├── api_service.py          # ★ Entry point: REST API + SocketIO server
│   ├── requirements.txt        # Backend Python dependencies
│   │
│   ├── agents/                 # AI Agent layer
│   │   ├── intent_agent.py     # Detect user intent
│   │   ├── planner_agent.py    # Generate execution plans
│   │   ├── safety_agent.py     # Risk-level assessment
│   │   └── tool_agent.py       # Select appropriate tools
│   │
│   ├── automation/             # Automation tools (49 tools)
│   │   ├── registry_tools.py   # ★ Central tool registration
│   │   ├── automation_router.py   # Command → tool routing
│   │   ├── base_tool.py           # Abstract base class for all tools
│   │   ├── app_launcher.py        # Launch desktop applications
│   │   ├── browser_control.py     # Browser automation (URL, search)
│   │   ├── whatsapp_desktop.py    # WhatsApp Desktop integration
│   │   ├── email_tool.py          # Email sending via SMTP
│   │   ├── window_detection.py    # Window focus / detection utils
│   │   ├── error_handler.py       # Unified error handling
│   │   │
│   │   ├── system/             # System-level tools
│   │   │   ├── volume.py       # Volume up / down / mute
│   │   │   ├── power.py        # Lock / shutdown / restart
│   │   │   ├── sleep.py        # Sleep / hibernate
│   │   │   ├── screenshot.py   # Fullscreen & region screenshots
│   │   │   ├── clipboard.py    # Copy / paste / clear clipboard
│   │   │   ├── display.py      # Brightness & monitor control
│   │   │   ├── window_manager.py  # Minimize / maximize / switch
│   │   │   └── shortcuts.py    # Task Manager, File Explorer, etc.
│   │   │
│   │   └── file/               # File & folder tools
│   │       ├── file_operations.py   # Create / open / delete / move
│   │       ├── folder_operations.py # Create / delete folders
│   │       ├── file_search.py       # Search files by name
│   │       └── delete_history.py    # In-memory deletion tracker
│   │
│   ├── auth/                   # Authentication
│   │   └── auth_service.py     # JWT tokens, bcrypt hashing, password reset
│   │
│   ├── config/                 # Configuration
│   │   ├── assistant_config.json  # LLM model, wake-word, timeout settings
│   │   ├── assistant_config.py    # Config loader
│   │   ├── settings.py            # App-wide constants
│   │   └── logger.py              # Logging setup
│   │
│   ├── core/                   # Orchestration layer
│   │   ├── assistant_controller.py  # ★ Command processing pipeline
│   │   ├── multi_executor.py        # Execute multi-step plans
│   │   ├── executor.py              # Execute a single tool call
│   │   ├── tool_registry.py         # Runtime tool registry
│   │   ├── tool_call.py             # Tool call data class
│   │   ├── execution_plan.py        # Plan data model
│   │   ├── translation_service.py   # Multi-language input/output
│   │   ├── command_parser.py        # Rule-based parser
│   │   ├── confidence_config.py     # Confidence thresholds
│   │   ├── confidence_tracker.py    # Per-session confidence tracking
│   │   ├── persona.py               # Assistant persona styles
│   │   └── exceptions.py            # Custom exception types
│   │
│   ├── database/               # Database layer
│   │   ├── __init__.py         # SQLAlchemy init + table creation
│   │   └── models.py           # User, Session, PasswordResetToken models
│   │
│   ├── llm/                    # LLM integration
│   │   ├── llm_client.py       # ★ Ollama client + keyword fallback planner
│   │   ├── intent_agent.py     # LLM-based intent classifier
│   │   ├── parameter_extractor.py  # Extract entities from commands
│   │   ├── parameter_validator.py  # Validate extracted params
│   │   ├── prompt.txt          # System prompt for LLM plan generation
│   │   ├── entities.json       # Known entity definitions
│   │   └── Modelfile           # Ollama custom model definition
│   │
│   ├── memory/                 # Session & persistent memory
│   │   ├── memory_store.py     # ★ Read/write persistent facts (JSON)
│   │   ├── session_state.py    # Live session state tracker
│   │   └── state_schema.py     # State schema definitions
│   │
│   ├── middleware/             # Request validation & authorization
│   │   ├── auth_middleware.py  # @login_required, @admin_required decorators
│   │   └── validation.py       # Marshmallow schemas for all endpoints
│   │
│   ├── voice_engine/           # Voice processing
│   │   ├── audio_pipeline.py   # ★ Full STT→process→TTS pipeline
│   │   ├── wake_word_detector.py   # Wake-word detection loop
│   │   ├── input/recorder.py   # Microphone audio recorder
│   │   ├── stt/whisper_engine.py   # Whisper speech-to-text
│   │   └── tts/tts_engine.py   # Piper text-to-speech
│   │
│   └── data/                   # Runtime data (gitignored content)
│       ├── .gitkeep            # Keeps directory in git
│       ├── audio/              # Recorded .wav files (gitignored)
│       ├── session_memory.json # Persistent user facts (gitignored)
│       └── delete_history.json # Deletion log (gitignored)
│
├── 🖥️ desktop_1/               ← CustomTkinter desktop client
│   ├── main.py                 # ★ Entry point — starts desktop UI
│   ├── requirements.txt        # Desktop Python dependencies
│   ├── config.py               # Desktop-side config
│   ├── settings_manager.py     # Persistent UI settings (~/.omniassist/)
│   │
│   ├── ui/                     # UI components
│   │   ├── chat_window.py      # ★ Main chat interface
│   │   ├── login_window.py     # Login form
│   │   ├── register_window.py  # Registration form
│   │   ├── forgot_password_window.py  # Password reset UI
│   │   ├── settings_modal.py   # Settings dialog (persona, language, theme)
│   │   ├── listening_overlay.py   # Siri-style voice overlay
│   │   ├── confirmation_popup.py  # High-risk action confirmation
│   │   ├── siri_orb.py         # Animated orb widget
│   │   ├── status_bar.py       # Connection/status bar
│   │   └── i18n.py             # UI string translations
│   │
│   ├── services/               # Backend communication
│   │   ├── api_client.py       # REST API client (JWT-aware)
│   │   └── socket_client.py    # SocketIO client (token-authenticated)
│   │
│   └── audio/
│       └── mic_visualizer.py   # Microphone level visualizer
│
├── 💻 cli/                     ← Terminal interfaces
│   ├── app.py                  # Full CLI voice loop
│   └── test.py                 # Simple backend test CLI
│
├── 📚 docs/                    ← All documentation
│   ├── README.md               # Docs index
│   ├── HANDBOOK.md             # Operational guide (runtime, memory, safety)
│   ├── API_DOCUMENTATION.md    # REST & WebSocket API reference
│   │
│   ├── guides/                 # User guides
│   │   ├── installation.md     # Full installation walkthrough
│   │   ├── security_setup.md   # Required env vars & security config
│   │   ├── email_setup.md      # SMTP config for email/password reset
│   │   ├── microphone_setup.md # Microphone troubleshooting
│   │   └── wake_word.md        # Wake-word detection guide
│   │
│   ├── reports/
│   │   └── REPORTS_SUMMARY.md  # Status index pointing to archive
│   │
│   └── archive/                # Historical docs (reference only)
│       ├── legacy-docs/        # Original documentation set
│       └── reports/            # Development status reports
│
├── 📖 examples/                ← Usage examples
│   ├── example_command_parser.py
│   ├── example_confidence_system.py
│   └── README.md
│
├── 🧪 tests/                   ← Automated test suite
│   ├── conftest.py             # Shared pytest fixtures
│   ├── test_automation_router.py
│   ├── test_command_parser.py
│   ├── test_confidence_config.py
│   ├── test_confidence_tracker.py
│   ├── test_error_handling.py
│   ├── test_file_operations.py
│   ├── test_intent_parser.py
│   ├── test_parameter_extraction.py
│   ├── test_parameter_validation.py
│   ├── test_password_reset.py
│   ├── test_stt_module.py
│   ├── test_tts_module.py
│   ├── README.md
│   └── manual/                 # Manual/integration tests
│       ├── test_voice.py
│       ├── test_wake_word.py
│       └── test_wake_word_integration.py
│
├── 📝 logs/                    ← Runtime logs (gitignored content)
│   └── .gitkeep
│
└── 🐍 venv/                    ← Python virtual environment (gitignored)
```

---

## Key Entry Points

| File | Purpose | When to Use |
|------|---------|-------------|
| `START.bat` | One-click launcher | Daily use |
| `launcher.bat` | Debug launcher | Troubleshooting startup |
| `backend/api_service.py` | Flask backend | Manual backend start |
| `desktop_1/main.py` | Desktop UI | Manual frontend start |
| `cli/app.py` | CLI voice loop | Terminal-only usage |
| `cli/test.py` | Quick backend test | Verifying backend is up |

---

## Required Environment Variables

Must be set before starting (see [docs/guides/security_setup.md](docs/guides/security_setup.md)):

```powershell
setx OMNIASSIST_FLASK_SECRET_KEY "your-long-random-string"
setx OMNIASSIST_JWT_SECRET       "your-long-random-string"
```

Optional (SMTP for password reset, see [docs/guides/email_setup.md](docs/guides/email_setup.md)):
```powershell
setx SMTP_HOST     "smtp.gmail.com"
setx SMTP_PORT     "587"
setx SMTP_USER     "you@gmail.com"
setx SMTP_PASSWORD "your-app-password"
```

---

## Important Configuration Files

| File | Purpose |
|------|---------|
| `backend/config/assistant_config.json` | LLM timeout, wake-word, model settings |
| `backend/config/settings.py` | App-wide constants |
| `backend/requirements.txt` | Backend Python packages |
| `desktop_1/requirements.txt` | Desktop Python packages |
| `requirements-test.txt` | Testing packages |
| `pytest.ini` | Test runner configuration |

---

## API Quick Reference

Full reference: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

**Authentication:**
- `POST /api/auth/login` — Login, returns JWT
- `POST /api/auth/register` — Create account
- `POST /api/auth/logout` — Invalidate token
- `GET  /api/auth/verify` — Verify token

**Commands:**
- `POST /api/process_command` — Execute a text command *(requires auth)*
- `POST /api/confirm` — Confirm a pending high-risk action *(requires auth)*
- `POST /api/speak` — Speak text via TTS *(requires auth)*

**Settings:**
- `GET  /api/settings` — Get current settings *(requires auth)*
- `POST /api/settings` — Update settings *(requires admin)*

**SocketIO Events (real-time):**
- `send_command` → server: send command via WebSocket *(requires auth token)*
- `command_result` → client: execution result
- `execution_step` → client: step-by-step progress
- `confirmation_required` → client: action needs confirmation
- `voice_input` → client: transcribed speech
- `listening_status` → client: microphone state

---

## Tool Categories (49 tools)

| Category | Count | Examples |
|----------|-------|---------|
| File Operations | 5 | create, open, delete, move, search |
| Folder Operations | 2 | create, delete |
| Browser | 3 | open URL, Google search, YouTube |
| Application Launcher | 1 | open Chrome / Notepad / Calculator |
| Communication | 4 | WhatsApp send, Email send |
| Volume Control | 3 | up, down, mute |
| Power Management | 5 | lock, shutdown, restart, sleep, hibernate |
| Screenshots | 2 | fullscreen, region |
| Clipboard | 3 | copy, paste, clear |
| Window Management | 5 | minimize, maximize, switch, task view |
| Display Control | 4 | brightness up/down/set, monitor off |
| System Shortcuts | 5 | Task Manager, File Explorer, Settings, Run, Recycle Bin |

Full tool list: [docs/archive/reports/AUTOMATION_STATUS_REPORT.md](docs/archive/reports/AUTOMATION_STATUS_REPORT.md)


## Directory Layout

```
AI-Based-Voice-Enabled-Intelligent-System-Assistant/
│
├── 📄 Root Files
│   ├── README.md              # Main documentation
│   ├── START.bat              # User launcher (simple)
│   ├── launcher.bat           # Developer launcher (debug)
│   ├── pytest.ini             # Pytest configuration
│   └── requirements-test.txt  # Test dependencies
│
├── 🔧 Backend (Core System)
│   ├── api_service.py         # Main entry: Flask API + SocketIO
│   ├── requirements.txt       # Backend Python dependencies
│   │
│   ├── agents/                # AI Agents
│   │   ├── intent_agent.py    # Detect user intent
│   │   ├── planner_agent.py   # Generate execution plans
│   │   ├── safety_agent.py    # Risk assessment
│   │   └── tool_agent.py      # Tool selection
│   │
│   ├── automation/            # All Automation Tools (49 total)
│   │   ├── automation_router.py    # Central dispatcher
│   │   ├── base_tool.py            # Tool base class
│   │   ├── app_launcher.py         # Launch applications
│   │   ├── browser_control.py      # Browser automation
│   │   ├── whatsapp_desktop.py     # WhatsApp integration
│   │   ├── email_tool.py           # Email sending
│   │   ├── file_manager.py         # Legacy file operations
│   │   ├── window_detection.py     # Window management utils
│   │   ├── error_handler.py        # Error handling
│   │   ├── registry_tools.py       # Tool registration
│   │   │
│   │   ├── system/            # System Control Tools
│   │   │   ├── volume.py      # Volume up/down/mute
│   │   │   ├── power.py       # Lock/shutdown/restart/sleep/hibernate
│   │   │   ├── screenshot.py  # Screenshots
│   │   │   ├── clipboard.py   # Clipboard operations
│   │   │   ├── display.py     # Brightness, monitor control
│   │   │   ├── window_manager.py  # Window minimize/maximize
│   │   │   ├── shortcuts.py   # System shortcuts (Task Manager, etc.)
│   │   │   └── sleep.py       # Sleep/hibernate
│   │   │
│   │   └── file/              # File Operations
│   │       ├── file_operations.py  # CRUD operations
│   │       ├── folder_operations.py # Folder CRUD
│   │       ├── file_search.py      # Search files
│   │       └── delete_history.py   # Track deletions
│   │
│   ├── config/                # Configuration
│   │   ├── assistant_config.json  # Main config file
│   │   ├── assistant_config.py    # Config loader
│   │   ├── logger.py              # Logging setup
│   │   └── settings.py            # App settings
│   │
│   ├── core/                  # Core Orchestration
│   │   ├── assistant_controller.py  # Main controller
│   │   ├── command_parser.py        # Parse commands
│   │   ├── executor.py              # Execute single tool
│   │   ├── multi_executor.py        # Execute multiple tools
│   │   ├── tool_registry.py         # Tool registry
│   │   ├── tool_call.py             # Tool call abstraction
│   │   ├── execution_plan.py        # Execution plan model
│   │   ├── confidence_config.py     # Confidence thresholds
│   │   ├── confidence_tracker.py    # Track confidence scores
│   │   ├── persona.py               # Voice persona styles
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── llm/                   # LLM Integration
│   │   ├── llm_client.py      # Ollama API client
│   │   ├── intent_agent.py    # Intent detection via LLM
│   │   ├── entities.json      # Entity definitions
│   │   └── intent.md          # Intent prompt template
│   │
│   ├── voice_engine/          # Voice Processing
│   │   ├── audio_pipeline.py  # Main audio pipeline
│   │   ├── stt_module.py      # Whisper STT
│   │   ├── tts_module.py      # Piper TTS
│   │   └── audio_utils.py     # Audio utilities
│   │
│   ├── memory/                # Session Management
│   │   ├── session_state.py   # Session state tracker
│   │   └── history.py         # Conversation history
│   │
│   └── data/                  # Runtime Data
│       ├── delete_history.json  # Deleted files log
│       └── audio/               # Recorded audio files
│
├── 🖥️ Desktop UI (Frontend)
│   ├── main.py                # Entry point
│   ├── requirements.txt       # Desktop dependencies
│   │
│   ├── ui/                    # UI Components
│   │   ├── chat_window.py     # Main chat interface
│   │   ├── listening_overlay.py  # Siri-style overlay
│   │   ├── status_bar.py      # Status indicators
│   │   └── mic_visualizer.py  # Audio visualization
│   │
│   ├── services/              # Backend Communication
│   │   ├── api_client.py      # REST API client
│   │   └── socket_client.py   # SocketIO client
│   │
│   └── audio/                 # Audio assets
│
├── 💻 CLI Interfaces
│   ├── app.py                 # Full CLI with voice confirmation
│   └── test.py                # Simple test CLI
│
├── 📚 Documentation
│   ├── API_DOCUMENTATION.md           # REST API reference
│   ├── SYSTEM_CAPABILITIES.md         # Feature list
│   ├── COMMAND_PARSING_SUMMARY.md     # Command parsing docs
│   ├── CONFIDENCE_SYSTEM_SUMMARY.md   # Confidence scoring
│   ├── TESTING_SUMMARY.md             # Testing guide
│   ├── COMPLETE_INSTALLATION_GUIDE.md # Full setup guide
│   ├── InstallationGuide.md           # Quick setup
│   ├── README.md                      # Docs overview
│   └── READMESummary.md              # Docs summary
│   │
│   └── reports/               # Development Reports
│       ├── AUTOMATION_STATUS_REPORT.md  # Tool integration status
│       ├── AUTOMATION_TEST_REPORT.md    # Test coverage report
│       ├── COMPLETE_FIX_REPORT.md       # Bug fix log
│       └── LLM_FIX_REPORT.md            # LLM optimization log
│
├── 📖 Examples
│   ├── example_command_parser.py      # Command parser usage
│   ├── example_confidence_system.py   # Confidence system demo
│   └── README.md                      # Examples guide
│
├── 🧪 Tests
│   ├── conftest.py                    # Pytest fixtures
│   ├── test_automation_router.py
│   ├── test_command_parser.py
│   ├── test_confidence_config.py
│   ├── test_confidence_tracker.py
│   ├── test_error_handling.py
│   ├── test_file_operations.py
│   ├── test_intent_parser.py
│   ├── test_parameter_extraction.py
│   ├── test_parameter_validation.py
│   ├── test_stt_module.py
│   ├── test_tts_module.py
│   └── README.md              # Testing guide
│
├── 📝 Logs (Auto-generated)
│   └── backend.log            # Runtime logs
│
└── 🐍 Virtual Environment
    └── venv/                  # Python packages
```

---

## Key Entry Points

| File | Purpose | Use When |
|------|---------|----------|
| `START.bat` | Launch desktop app | Regular use |
| `launcher.bat` | Debug mode launcher | Troubleshooting |
| `backend/api_service.py` | Flask API server | Running backend manually |
| `desktop_1/main.py` | Desktop UI | Running frontend manually |
| `cli/app.py` | CLI voice loop | Terminal-only usage |
| `cli/test.py` | Quick test | Testing backend |

---

## Important Configuration Files

| File | Purpose |
|------|---------|
| `backend/config/assistant_config.json` | LLM timeout, model settings |
| `backend/config/settings.py` | App-wide constants |
| `pytest.ini` | Test configuration |
| `backend/requirements.txt` | Backend Python packages |
| `desktop_1/requirements.txt` | Desktop Python packages |
| `requirements-test.txt` | Testing packages |

---

## API Endpoints

See [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for full reference.

**Key endpoints:**
- `GET /api/status` - System status
- `POST /api/process_command` - Execute command
- `GET /api/health` - Health check
- `POST /api/start_listening` - Start voice mode
- `POST /api/stop_listening` - Stop voice mode
- `POST /api/confirm` - Confirm pending action

**SocketIO Events:**
- `voice_input` - Transcribed voice
- `command_result` - Execution result
- `execution_step` - Step progress
- `confirmation_required` - Needs confirmation
- `listening_status` - Listening state
- `error` - Error messages

---

## Tool Categories

See [docs/reports/AUTOMATION_STATUS_REPORT.md](docs/reports/AUTOMATION_STATUS_REPORT.md) for complete tool list.

**49 automation tools organized in:**
- Communication (WhatsApp, Email)
- Applications (Launcher)
- Browser (URL, search, YouTube)
- Volume Control
- Power Management
- Screenshots
- Clipboard
- Window Management
- Display Control
- System Shortcuts
- File Operations
- Folder Operations
- File Search

---

## Development Workflow

1. **Add New Tool**: Create in `backend/automation/`, register in `registry_tools.py`
2. **Modify UI**: Edit `desktop_1/ui/chat_window.py`
3. **Add API Endpoint**: Modify `backend/api_service.py`
4. **Add Tests**: Create `tests/test_*.py`
5. **Update Config**: Edit `backend/config/assistant_config.json`

---

**Last Updated**: March 6, 2026
