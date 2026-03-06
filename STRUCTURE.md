# Project Structure Reference

Quick reference guide for navigating the codebase.

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
