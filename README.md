# 🧠 AI-Based Voice-Enabled Intelligent System (Windows)

A modular, production-ready AI voice assistant for Windows desktop automation.

This system combines:

- 🎙 Offline Speech-to-Text (Whisper)
- 🔊 Offline Text-to-Speech (Piper)
- ⚙ Agent-Based Automation Engine
- 🧩 Tool Registry & Executor Architecture
- 🖥 System + File + Application Automation

---

## 🚀 Architecture Overview

Voice Input (Whisper - GPU)
↓
Audio Pipeline
↓
Assistant Controller
↓
Agent / Planner
↓
Tool Registry
↓
Automation Tool Execution
↓
Voice Response (Piper TTS)


The system is fully modular and designed for scalability and future LLM integration.

---

## 📁 Project Structure

backend/
│
├── voice_engine/ # STT, TTS, audio pipeline
│ ├── input/
│ ├── stt/
│ ├── tts/
│ └── audio_pipeline.py
│
├── automation/ # All automation tools
│ ├── base_tool.py
│ ├── system/
│ ├── file/
│ ├── whatsapp_desktop.py
│ └── ...
│
├── core/ # Agent, Executor, Tool Registry
│ ├── assistant_controller.py
│ ├── agent.py
│ ├── executor.py
│ └── tool_registry.py
│
├── config/ # Logger & settings
│
└── data/ # Runtime storage (ignored in git)


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

📌 Status
Production-ready local automation system with scalable agent architecture.


---

# 🔥 This README Is:

- Clean
- Professional
- Evaluator-friendly
- Architecture-focused
- Industry-level structured

---

If you want, I can also:

- Create a **high-impact GitHub landing header**
- Add architecture diagram image
- Make it more research-paper style
- Or make it startup-style product README**

Tell me the vibe you want.
