<<<<<<< HEAD
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
=======
# Ollama Intent Engine

A local intent classification and entity extraction system powered by a custom Ollama model (LLaMA 3 8B). It parses natural-language user commands into structured JSON, then routes them to the appropriate executor via a planner.

## Architecture

```
User Command
     │
     ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Prompt  │───▶│  Ollama  │───▶│ Planner  │───▶ Executor
│ Template │    │  Model   │    │ (Router) │
└──────────┘    └──────────┘    └──────────┘
                                     │
                              ┌──────┴──────┐
                              │  Entities   │
                              │  Validation │
                              └─────────────┘
```

1. **Prompt** (`prompt.txt`) — Instructs the LLM to classify the user's command into an intent and extract entities.
2. **Model** (`Modelfile`) — A deterministic Ollama model built on `llama3:8b` with low temperature/top-p to ensure consistent, JSON-only output.
3. **Planner** (`planner.py`) — Validates the LLM response (confidence, entities) and dispatches to the correct executor function.

## Files

| File | Purpose |
| --- | --- |
| `Modelfile` | Ollama model definition — base model, parameters, and system prompts |
| `prompt.txt` | Prompt template sent to the model with the user's command |
| `entities.json` | Schema defining required/optional entities per intent |
| `intent.md` | Frozen intent taxonomy — the single source of truth for allowed intents |
| `planner.py` | Decision engine that validates and routes LLM output to executors |

## Supported Intents

| Intent | Required Entities | Optional Entities | Example |
| --- | --- | --- | --- |
| `open_application` | `application` | — | *"Open Spotify"* |
| `open_application_and_navigate` | `application`, `url` | — | *"Open Chrome and go to YouTube"* |
| `play_music` | `song` | `artist` | *"Play Bohemian Rhapsody by Queen"* |
| `get_weather` | `location` | — | *"What's the weather in Tokyo?"* |
| `get_fact` | `subject`, `fact_type` | — | *"Tell me a fun fact about Mars"* |
| `get_definition` | `topic` | — | *"Define machine learning"* |
| `get_tips` | `topic` | — | *"Give me tips on public speaking"* |
| `unknown` | — | — | Anything that doesn't match above |

## Model Configuration

Defined in `Modelfile`:

| Parameter | Value | Reason |
| --- | --- | --- |
| `temperature` | 0.0 | Deterministic output — no creativity needed |
| `top_p` | 0.5 | Narrow token sampling for consistency |
| `repeat_penalty` | 1.2 | Prevents repetitive tokens in output |
| `num_ctx` | 2048 | Context window size |

The model is constrained via system prompts to:

- Output **only** valid JSON (no markdown, no explanations)
- Cap confidence between **0.0 and 0.95** (never 1.0)

## LLM Output Schema

The model returns a single JSON object:

```json
{
  "intent": "open_application_and_navigate",
  "entities": {
    "application": "chrome",
    "url": "https://www.youtube.com"
  },
  "confidence": 0.92
}
```

## Planner Logic

`planner.py` processes the LLM output through these steps:

1. **Confidence check** — If `confidence < 0.7`, ask for clarification.
2. **Unknown intent** — If intent is `unknown`, ask for clarification.
3. **Entity validation** — Checks that all required entities (defined in `entities.json`) are present.
4. **Dispatch** — Routes to the matching executor function (e.g., `open_application()`, `play_music()`).

## Setup

### Prerequisites

- [Ollama](https://ollama.com/) installed and running locally

### Create the Model

```bash
ollama create intent-engine -f Modelfile
```

### Run a Query

```bash
ollama run intent-engine "Open Chrome and go to YouTube"
```

The model will return a JSON object that can be passed directly to `planner.plan()`.

## Adding a New Intent

1. Add the intent name to `intent.md`.
2. Define its required/optional entities in `entities.json`.
3. Add a handler branch in `planner.py`.
4. Update the `ALLOWED INTENTS` list in `prompt.txt`.
5. Implement the corresponding executor function.
>>>>>>> swayam_ai
