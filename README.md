# 🧠 AI-Based Voice-Enabled Intelligent System (Windows)

A modular, production-ready AI voice assistant for Windows desktop automation.

This system combines:

- 🎙 Offline Speech-to-Text (Whisper)
- 🔊 Offline Text-to-Speech (Piper)
- 🤖 LLM Integration (Ollama)
- ⚙ Agent-Based Automation Engine
- 🧩 Tool Registry & Executor Architecture
- 🖥 System + File + Application Automation

---

## 🚀 Architecture Overview

```
Voice Input (Whisper - GPU)
        ↓
Audio Pipeline
        ↓
Assistant Controller
        ↓
Agent / Planner (Ollama LLM)
        ↓
Tool Registry
        ↓
Automation Tool Execution
        ↓
Voice Response (Piper TTS)
```

The system is fully modular and designed for scalability and LLM integration.

---

## 📁 Project Structure

```
AI-Based-Voice-Enabled-Intelligent-System-Assistant/
│
├── app.py                    # Main entry point
├── README.md                 # This file
├── pytest.ini                # Test configuration
├── requirements-test.txt     # Test dependencies
│
├── backend/                  # Core system code
│   ├── voice_engine/         # STT, TTS, audio pipeline
│   │   ├── input/
│   │   ├── stt/
│   │   ├── tts/
│   │   └── audio_pipeline.py
│   │
│   ├── automation/           # All automation tools
│   │   ├── base_tool.py
│   │   ├── system/
│   │   ├── file/
│   │   ├── whatsapp_desktop.py
│   │   └── ...
│   │
│   ├── core/                 # Agent, Executor, Tool Registry
│   │   ├── assistant_controller.py
│   │   ├── command_parser.py
│   │   ├── executor.py
│   │   ├── multi_executor.py
│   │   ├── tool_registry.py
│   │   └── ...
│   │
│   ├── llm/                  # LLM integration (Ollama)
│   │   ├── llm_client.py
│   │   ├── Modelfile
│   │   └── ...
│   │
│   ├── config/               # Logger & settings
│   ├── memory/               # Session & state management
│   └── data/                 # Runtime storage
│
├── tests/                    # Comprehensive test suite
│   ├── test_command_parser.py
│   ├── test_confidence_tracker.py
│   └── ...
│
├── docs/                     # Detailed documentation
│   ├── COMPLETE_INSTALLATION_GUIDE.md
│   ├── COMMAND_PARSING_SUMMARY.md
│   ├── CONFIDENCE_SYSTEM_SUMMARY.md
│   └── ...
│
└── examples/                 # Demo scripts
    ├── example_command_parser.py
    └── example_confidence_system.py
```


---

## 🎙 Voice Capabilities

### ✅ Speech-to-Text
- OpenAI Whisper (GPU enabled)
- English-only transcription
- Deterministic configuration
- Push-to-talk support

### ✅ Text-to-Speech
- Piper TTS (offline)
- Custom tuning parameters:
  - `length_scale`
  - `noise_scale`
  - `noise_w`
- Runtime audio cleanup

---

## ⚙ Automation Capabilities

### 🖥 System Control
- Lock laptop
- Shutdown
- Restart
- Volume up/down
- Mute

### 📂 File Operations
- Open file
- Create file
- Delete file
- Move file
- Create folder
- Delete folder
- Search file

### 📱 Application Automation
- Open WhatsApp Desktop
- Send WhatsApp message
- Launch applications
- Browser control

All automation tools follow:

BaseTool → ToolRegistry → Executor


This allows easy addition of new tools without modifying core logic.

---

## 🧩 Agent-Based Execution Model

Each command is converted into:

python
ToolCall(
    name="file.open",
    args={"path": "C:/Users/..."}
)
Then executed through:

Executor → ToolRegistry → Tool.execute()
No hardcoded spaghetti IF-ELSE chains.

🛠 Setup Instructions
1️⃣ Clone Repository
git clone https://github.com/your-repo-link
cd AI-Based-Voice-Enabled-Intelligent-System-Assistant
2️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate
3️⃣ Install Dependencies
pip install -r requirements.txt
4️⃣ Run Assistant
python app.py
🎮 Usage
When running:

Hold SPACE → Voice input

Press CTRL + T → Text input

Say/type:

"Open WhatsApp"

"Lock my laptop"

"Shutdown system"

"Create folder test in documents"

"Send hello to Swayam on WhatsApp"

Say:

exit
to terminate assistant.

🧠 Design Principles
Fully offline for core features

Modular & production-ready

Tool-based architecture

Thread-safe ready

LLM-integration ready

Clean separation of concerns

🔒 Security
No cloud dependency for automation

No remote command execution

All operations run locally on Windows

🏗 Future Improvements
LLM-based intent parsing

GUI dashboard

Context memory

Multi-step planning

Advanced permission system

👨‍💻 Authors
Voice & Automation Core: Vansh Raghav

LLM Integration: Team Member

UI & Deployment: Team Member

---

## 📚 Documentation

For detailed guides and documentation, see the [docs/](docs/) directory:

- **[Complete Installation Guide](docs/COMPLETE_INSTALLATION_GUIDE.md)** - Full setup instructions
- **[Command Parsing System](docs/COMMAND_PARSING_SUMMARY.md)** - How commands are processed
- **[Confidence System](docs/CONFIDENCE_SYSTEM_SUMMARY.md)** - Confidence tracking and scoring
- **[Testing Guide](docs/TESTING_SUMMARY.md)** - Test coverage and framework

---

## 🎯 Examples

Check out the [examples/](examples/) directory for:
- Interactive command parser demonstration
- Confidence system demonstration
- Testing various system features

---

## 📌 Status

Production-ready AI voice assistant with:
- ✅ Offline speech processing
- ✅ LLM integration (Ollama)
- ✅ Comprehensive automation tools
- ✅ Full test coverage
- ✅ Safety confirmations for critical operations