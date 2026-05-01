# OMINI Assistant AI - Full Developer Understanding Report

Update note:
- This report is now complemented by two focused deep-dive documents:
  - `BACKEND_DEEP_UNDERSTANDING.md`
  - `FRONTEND_DEEP_UNDERSTANDING.md`
- Use this file as the broad system report and the two new files for implementation-level depth.

## 1. Purpose and Scope
This report explains how the current codebase works end to end, including:
- Startup and runtime behavior
- Online and offline execution paths
- Module responsibilities
- Tool/action contracts
- Data storage and configuration
- Error handling and recovery
- Gaps, risks, and technical debt

It is written for developers who need to maintain, debug, or extend the project.

## 2. High-Level Architecture
The system is a voice-first desktop assistant with a GUI and tool-calling backend.

Core runtime layers:
1. UI layer (`ui.py`): desktop visualization, status states, typed command input, setup dialog.
2. Orchestrator (`main.py`): Gemini Live session, audio streaming, tool dispatch, memory injection, offline fallback.
3. Tool layer (`actions/*.py`): executable capabilities (apps, files, browser, reminders, system control, etc.).
4. Memory layer (`memory/memory_manager.py`): local long-term memory persistence and prompt formatting.
5. Offline voice bridge (`voice/offline_bridge.py`): local STT/TTS and local model routing when internet is down.

Secondary agent stack (present but not the primary live path):
- `agent/planner.py`
- `agent/executor.py`
- `agent/error_handler.py`
- `agent/task_queue.py`

This stack is used when `agent_task` is called, and by specific actions (`dev_agent`, `code_helper`) that do their own generation/execution workflows.

## 2A. Full Tech Stack and Framework Usage (What + How)
This section is the explicit stack inventory requested by developers: what technology is in this codebase, where it is used, and how it is used in runtime behavior.

### 2A.1 Language and Runtime
- Python 3.x: Entire codebase is Python.
- Async runtime (`asyncio`): Core live orchestration in `main.py` (audio send/receive/play task group).
- Threads (`threading`): UI-to-backend bridging, background task queue workers, non-blocking command handlers.
- Subprocess execution (`subprocess`): OS integration, scheduler registration, app launching, external tool calls.

### 2A.2 AI/LLM Frameworks and Services
- Google Gen AI SDK (`google-genai`): Used in `main.py` for Gemini Live native audio sessions and function-calling tools.
- Google Generative AI SDK (`google-generativeai`): Used in planner/executor/actions for text generation, repair loops, parsing, and intent detection.
- Gemini models used:
  - `models/gemini-2.5-flash-native-audio-preview-12-2025`: Live voice conversation + tool calls.
  - `gemini-2.5-flash` / `gemini-2.5-flash-lite`: planning, summarization, translation, intent detection, extraction.
  - `gemini-2.0-flash`: used in one error-fix generation path in `agent/error_handler.py`.
- Ollama local LLM API: Used in `voice/offline_bridge.py` to route offline turns (`/api/chat`) when internet is down.

How this is used:
- Online path: Gemini Live decides tool calls from declared schemas, system executes tools, sends tool results back, Gemini voices answer.
- Offline path: Local STT transcribes command, Ollama decides respond/tool mode, local tool executes, Piper speaks response.

### 2A.3 UI Framework
- PySide6 (Qt for Python): Full desktop interface in `ui.py`.

How this is used:
- Custom animated assistant face/orb rendering with `QPainter`.
- Signal/slot pattern for thread-safe log/state updates (`log_requested`, `state_requested`).
- Input command bar + send button + mute toggle + setup dialog for first boot.

### 2A.4 Audio and Speech Stack
- `sounddevice`: Microphone capture and speaker playback in online and offline flows.
- `numpy` + `scipy`: Audio arrays, WAV writing/reading, signal utilities.
- Offline STT engines:
  - `faster-whisper` (preferred)
  - `openai-whisper` (fallback)
- `torch`: backend dependency for whisper model execution.
- Piper TTS (bundled model files): local text-to-speech in offline mode.

How this is used:
- Live mode: stream mic PCM to Gemini and play returned PCM audio.
- Offline mode: record short chunk -> transcribe locally -> generate plan/response -> synthesize and play local speech.

### 2A.5 Browser and Web Automation Stack
- Playwright: Browser automation in `actions/browser_control.py`.
- Browser session architecture: persistent context per browser with profile reuse.
- `requests`: HTTP fetches (YouTube scraping, Ollama checks, etc.).
- DuckDuckGo search client (`duckduckgo-search`/`ddgs`): fallback search source.

How this is used:
- High-level web actions (`go_to`, `search`, `click`, `type`, `smart_click`, `smart_type`, `tabs`, `screenshots`) are abstracted behind one tool.
- For browser-critical features (flights/youtube info), actions combine browser automation + model parsing.

### 2A.6 Desktop/OS Automation Stack
- `pyautogui`: keyboard/mouse automation across many actions.
- `pyperclip`: clipboard-safe text injection for robust typing.
- `psutil`: process inspection support where needed.
- Optional helpers: `pywinauto`, `pygetwindow`, `send2trash` used conditionally by feature.

How this is used:
- Application launching fallback, message sending automation, system shortcut execution, install dialogs, screen interactions.
- File operations are constrained by safe root checks in `actions/file_controller.py`.

### 2A.7 Vision and Image Processing Stack
- `mss`: fast screen capture in `actions/screen_processor.py`.
- OpenCV (`cv2`): webcam capture and camera probing.
- Pillow (`PIL`): image conversion/compression before sending to model.

How this is used:
- Capture screen/camera, compress image, send image + prompt to Gemini live session, play spoken analysis result.

### 2A.8 Scheduling and System Integration
- Windows Task Scheduler (`schtasks`) for reminders and scheduled game updates.
- macOS launchd (`launchctl`) for reminders/schedules.
- Linux `systemd-run` or `at`/`cron` fallbacks.

How this is used:
- Time-based reminder scripts and recurring game update automation are registered with native OS schedulers.

### 2A.9 Packaging, Setup, and Project Execution
- `requirements.txt`: Python dependency lock source (broad, runtime-focused list).
- `setup.py`: convenience installer script (pip install requirements + playwright browser install).

How this is used:
- Developer runs setup once, then starts assistant via `python main.py`.

### 2A.10 Data Storage and Config Model
- Local JSON config: `config/api_keys.json`.
- Local JSON long-term memory: `memory/long_term.json`.
- Prompt file: `core/prompt.txt`.

How this is used:
- Config controls API key, OS mode, camera index.
- Memory is injected into live system instruction to personalize responses.
- Prompt file defines assistant routing/behavior policy.

### 2A.11 Internal Framework Patterns (Project-Level)
Even without a web framework, the project uses consistent internal architecture patterns:
- Tool-calling orchestration pattern: schema-declared tools + explicit dispatch in `main.py`.
- Action module pattern: each capability isolated under `actions/` with a normalized function signature.
- Planner/executor agent pattern: `agent/` package for multi-step goals, retries, replans.
- Queue/worker pattern: `agent/task_queue.py` priority queue and background execution.
- Offline bridge pattern: local fallback pipeline in `voice/offline_bridge.py`.

### 2A.12 External Platforms and Protocols Used
- Gemini Live API (audio + tool call protocol).
- Ollama HTTP API (`/api/tags`, `/api/chat`).
- Google Search tool integration via Gemini config.
- YouTube/Steam/Epic flows through a mix of official/open endpoints and UI-driven automation.

## 3. Entry Point and Boot Sequence
Main entry is `main.py`.

Boot order:
1. Resolve base directory (`get_base_dir`) to support both source mode and frozen executable mode.
2. Create `OminiUI` instance (`ui = OminiUI("face.png")`).
3. Start a background thread that:
   - Waits for API key setup (`ui.wait_for_api_key()`)
   - Instantiates `OminiLive(ui)`
   - Runs async event loop with `asyncio.run(omini.run())`
4. Run GUI event loop in main thread (`ui.run()`).

Important startup dependencies:
- `config/api_keys.json` must contain `gemini_api_key`.
- UI first-run setup also writes `os_system` in same file.

## 4. Runtime Modes
The orchestrator has two modes:
- Online Live mode (Gemini Live native audio)
- Offline fallback mode (local STT/TTS + optional Ollama command planner)

Mode switching logic:
- In `OminiLive.run()`, internet is checked via `OfflineVoiceBridge.has_internet()`.
- If offline: `_run_offline_mode()` loop handles local voice turns.
- If online: connect to Gemini Live session and run full duplex audio + tools.

## 5. Online Mode Detailed Flow
### 5.1 Session configuration
`_build_config()` in `main.py` creates `types.LiveConnectConfig` with:
- `response_modalities=["AUDIO"]`
- input/output audio transcription enabled
- tool declarations (`TOOL_DECLARATIONS`)
- system instruction = current time context + formatted memory + core prompt
- voice config (`Charon`)

### 5.2 Concurrent tasks in live mode
After successful connect, `main.py` starts 4 async tasks:
1. `_send_realtime()`: sends microphone chunks to live session.
2. `_listen_audio()`: reads microphone stream via `sounddevice.InputStream`.
3. `_receive_audio()`: consumes model responses, transcripts, and tool calls.
4. `_play_audio()`: plays assistant audio output to speakers.

### 5.3 Audio gating
`_listen_audio()` suppresses mic forwarding while assistant is speaking using `_is_speaking` lock state. This avoids immediate feedback loop and self-hearing.

### 5.4 Turn logging and UX
`_receive_audio()` accumulates input/output transcript chunks and logs full turns to UI when `turn_complete` arrives.

### 5.5 Tool call execution
When Gemini emits tool calls:
- `_receive_audio()` iterates each function call
- Calls `await _execute_tool(fc)`
- Sends `FunctionResponse` back via `send_tool_response`

Tool dispatch is implemented as explicit name-based branching in `_execute_tool`.
Most tool implementations run in thread pool via `loop.run_in_executor` to avoid blocking async loop.

## 6. Offline Mode Detailed Flow
Offline components are in `voice/offline_bridge.py` and `main.py` offline methods.

### 6.1 Offline capabilities
- Internet check with socket + HTTPS probes
- Local STT backend selection:
  - `faster-whisper` preferred
  - fallback to `openai-whisper`
- Local TTS via bundled Piper model files
- Optional local LLM routing via Ollama (`/api/chat`)

### 6.2 Offline command handling
`_run_offline_mode()` loop:
1. Listen + transcribe one short chunk (`listen_and_transcribe_once`).
2. Route command through `plan_offline_turn(...)`.
3. If planner returns `mode=tool`, execute only whitelisted offline tools.
4. Speak reply with Piper.
5. If local model unavailable, queue command for online replay.

Offline allowed tools are constrained to:
- `open_app`
- `computer_settings`
- `file_controller`
- `desktop_control`
- `computer_control`
- `reminder`
- `shutdown_omini`

### 6.3 Replay behavior
Queued offline text turns are replayed to Gemini once internet is restored (`_replay_offline_turns`).

## 7. Tool Declaration Layer
`main.py` contains large `TOOL_DECLARATIONS` list that defines function-calling schema for Gemini.

Key tools exposed:
- App/system: `open_app`, `computer_settings`, `computer_control`, `desktop_control`
- Web/browser: `web_search`, `browser_control`, `youtube_video`, `flight_finder`
- Files and productivity: `file_controller`, `reminder`, `send_message`
- Development: `code_helper`, `dev_agent`, `agent_task`
- Vision: `screen_process`
- Games: `game_updater`
- Lifecycle/memory: `shutdown_omini`, `save_memory`

Special behavior:
- `save_memory` is intentionally silent in `_execute_tool` and does not produce user-facing speech.

## 8. UI Layer (`ui.py`)
`OminiUI` is a fixed-size PySide6 desktop interface with:
- Animated central orb/face
- Log panel with typing animation
- Text input command bar
- Mute/live toggle
- State indicators (`LISTENING`, `THINKING`, `SPEAKING`, `PROCESSING`, `MUTED`)
- First-run initialization dialog for API key and OS selection

UI-thread safety pattern:
- Uses Qt signals (`log_requested`, `state_requested`) to marshal updates safely.

Termination behavior:
- `closeEvent` calls `os._exit(0)` for hard process exit.

## 9. Memory Layer
`memory/memory_manager.py` provides long-term personal memory with categories:
- identity
- preferences
- projects
- relationships
- wishes
- notes

Storage file:
- `memory/long_term.json`

Behavior highlights:
- Value truncation (`MAX_VALUE_LENGTH = 380`)
- Total serialized memory trimming (`MEMORY_MAX_CHARS = 2200`)
- Timestamped updates per entry (`updated` date)
- Prompt formatting with section limits to keep context compact

In live orchestration:
- Memory is loaded each session config build
- Memory string is prepended to system prompt
- `save_memory` tool writes updates directly

## 10. Agent Stack (Planner/Executor/Error Handler)
The `agent/` package supports multi-step autonomous tasks.

### 10.1 Planner (`agent/planner.py`)
- Uses Gemini text model to produce JSON plan (`goal`, `steps`)
- Has strict prompt rules and fallback plan (`web_search` single step)
- Includes `replan(...)` for failed-step recovery

### 10.2 Executor (`agent/executor.py`)
- Executes plan steps in sequence
- Calls mapped tools
- Retries each step up to 3 attempts
- Injects prior result context into some file writes
- Can translate injected content to user language
- Replans up to `MAX_REPLAN_ATTEMPTS = 2`

### 10.3 Error handler (`agent/error_handler.py`)
- Uses Gemini to classify failure into:
  - retry
  - skip
  - replan
  - abort
- Can propose replacement step via `generate_fix(...)`

### 10.4 Task queue (`agent/task_queue.py`)
- Background queue with task priority and cancellation
- Uses single concurrent worker by default
- `agent_task` tool in `main.py` submits jobs here

## 11. Actions Layer by Module
### 11.1 `actions/open_app.py`
Cross-platform app launcher with alias map and fallback launch strategies (direct command, URI, OS search UI).

### 11.2 `actions/web_search.py`
Primary search through Gemini Google Search tool; fallback to DuckDuckGo results formatting.

### 11.3 `actions/weather_report.py`
Opens weather search in browser via Google query URL.

### 11.4 `actions/send_message.py`
Desktop automation messaging flow using PyAutoGUI for WhatsApp/Telegram/Instagram/etc.

### 11.5 `actions/reminder.py`
Schedules reminders using OS-native schedulers:
- Windows Task Scheduler
- macOS launchd
- Linux systemd-run/at

### 11.6 `actions/computer_settings.py`
High-level system actions (volume, brightness, window/tab controls, wifi, power actions) with intent detection fallback via Gemini.

### 11.7 `actions/computer_control.py`
Low-level desktop control (click/type/hotkey/scroll/screenshot/window focus/screen find). Includes AI element localization using screenshot + Gemini.

### 11.8 `actions/file_controller.py`
File operations within safe roots (`Path.home()` scoped).
Supports list/create/delete/move/copy/rename/read/write/find/largest/disk_usage/organize/info.
Deletion prefers trash (`send2trash`), protects critical top-level dirs.

### 11.9 `actions/browser_control.py`
Persistent Playwright browser sessions per browser type.
Features:
- Multi-browser session registry
- Real profile reuse if available
- Actions for navigation, search, click/type, smart element interactions, tabs, screenshots

### 11.10 `actions/desktop.py`
Desktop organization, wallpaper operations, listing/stats, and AI-generated safe desktop task code with a constrained sandbox.

### 11.11 `actions/code_helper.py`
Code assistant operations:
- write/edit/explain/run/build/optimize/screen_debug
- build mode iteratively fixes runtime errors up to max attempts
- screen_debug captures screenshot and asks Gemini to diagnose visible errors

### 11.12 `actions/dev_agent.py`
Project generator:
- Plans file graph with Gemini
- Writes files in dependency-aware order
- Installs dependencies
- Runs and auto-fixes errors iteratively
- Opens project in VS Code

### 11.13 `actions/flight_finder.py`
Google Flights workflow:
- Parse date expressions
- Open flights page via browser control
- Extract page text
- Parse options with Gemini
- Optionally save report to desktop

### 11.14 `actions/game_updater.py`
Steam/Epic helper:
- Detect installation paths
- List/update/install games
- Schedule update jobs
- Optional shutdown when updates finish
- Windows-specific install dialog automation fallback paths

### 11.15 `actions/screen_processor.py`
Separate live vision-audio session to Gemini:
- Captures screen via `mss` or camera via OpenCV
- Compresses image
- Sends image + prompt to live model
- Plays spoken answer and logs transcript

### 11.16 `actions/youtube_video.py`
YouTube operations:
- play (search + open)
- summarize (transcript + Gemini summary)
- get_info
- trending

## 12. Configuration and Data Files
Primary configuration:
- `config/api_keys.json`

Expected keys used across modules:
- `gemini_api_key`
- `os_system`
- `camera_index` (set by vision module)

Prompt and behavior config:
- `core/prompt.txt` (core protocol instructions)

Memory data:
- `memory/long_term.json`

## 13. Dependencies and Setup
From `requirements.txt`, core dependencies include:
- Gemini SDKs: `google-genai`, `google-generativeai`
- Audio: `sounddevice`, `scipy`, `numpy`
- UI: `PySide6`
- Automation: `playwright`, `pyautogui`, `pyperclip`, `psutil`, `pynput`
- Search/media: `duckduckgo-search`, `yt-dlp`
- STT: `faster-whisper`, `openai-whisper`, `torch`

Setup helper:
- `setup.py` installs requirements and runs `playwright install`.

## 14. Error Handling and Resilience
Main runtime resilience patterns:
- Live session reconnect loop in `main.py` with delay
- Offline fallback on internet loss
- Non-blocking tool execution using executor threads
- Agent stack retry/replan/abort logic
- Broad exception catches in many action modules to keep assistant responsive

Tradeoff:
- Wide exception handling reduces crashes but can hide root causes unless logs are monitored.

## 15. Known Gaps, Inconsistencies, and Technical Debt
1. Mixed architecture generations:
- Live tool-calling path in `main.py` is primary.
- Agent planner/executor path is secondary and partially overlaps behavior.
- This duplicates logic and increases maintenance complexity.

2. Prompt/tool policy inconsistencies:
- `agent/planner.py` says never use generated code.
- `agent/executor.py` still supports `generated_code` fallback paths.

3. Missing package namespace for legacy voice modules:
- Files under `voice/input`, `voice/stt`, `voice/tts` import `backend.utils.*`, which is not present in this repository.
- These modules are not currently the active offline path.

4. Security/safety surface:
- Several actions execute OS automation with broad authority (keyboard/mouse/process/scheduler).
- `desktop.py` includes model-generated code execution in sandbox; safer than raw exec, but still a high-risk area.

5. Hard process exits:
- UI close and shutdown paths use `os._exit(0)` which bypasses graceful resource cleanup.

6. Config coupling:
- Many modules independently read `config/api_keys.json`, creating duplicated config access logic.

## 16. End-to-End Example Flows
### 16.1 Online command example ("open notepad")
1. User speaks or types command.
2. Input is sent to Gemini Live session.
3. Model chooses `open_app` tool call with `app_name`.
4. `main.py::_execute_tool` dispatches to `actions/open_app.py`.
5. Result is returned via `FunctionResponse`.
6. Model speaks completion audio; transcript appears in UI log.

### 16.2 Offline command example (same command while offline)
1. `_run_offline_mode()` captures short audio and transcribes locally.
2. `plan_offline_turn()` uses Ollama planner prompt.
3. If tool mode and tool is allowed, `open_app` executes locally.
4. Reply is spoken via Piper.
5. If local model unavailable, command is queued for replay when internet returns.

## 17. How to Extend Safely
Recommended extension path:
1. Add tool declaration in `main.py` (`TOOL_DECLARATIONS`).
2. Add implementation in `actions/`.
3. Add dispatch branch in `OminiLive._execute_tool`.
4. If offline support is needed, add tool to `_offline_allowed_tools` and `_execute_offline_tool`.
5. Update planner prompts only if `agent_task` workflows must understand the new tool.

## 18. Debugging Checklist
When behavior is broken, check in this order:
1. `config/api_keys.json` has valid `gemini_api_key` and `os_system`.
2. Internet reachability for live mode.
3. Microphone/speaker device access for `sounddevice`.
4. Playwright browser installation (`python -m playwright install`).
5. Tool-specific dependencies (for example `pyautogui`, STT packages).
6. Console logs from `main.py` and action modules.
7. If offline path fails, verify Piper files and optional Ollama endpoint.

## 19. Suggested Refactor Priorities
1. Consolidate configuration loading into one shared config service.
2. Decide on one planning/execution architecture and de-duplicate overlapping logic.
3. Formalize action interface and structured error/result schema.
4. Replace broad `except Exception` blocks with typed exceptions where practical.
5. Add integration tests for online tool dispatch and offline fallback routing.
6. Isolate high-risk automation/code-exec modules with stricter guards.

## 20. Practical Summary
The system is production-like in capability breadth and robust in fallback behavior, with `main.py` as the true runtime authority. Most user-visible behavior comes from live Gemini tool calls into `actions/*`. Offline fallback is functional and self-contained through `voice/offline_bridge.py`. The biggest maintenance challenge is architectural overlap (live tool orchestration vs. separate planner/executor stack) and uneven module maturity across action implementations.
