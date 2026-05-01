# OMINI Backend Deep Technical Understanding

## 1. Scope
This document is a deep technical reference for the backend/runtime side of OMINI.
It covers orchestration, tool dispatch, agent stack, memory, offline voice fallback, concurrency model, and extension points.

Primary source modules:
- main.py
- agent/planner.py
- agent/executor.py
- agent/error_handler.py
- agent/task_queue.py
- memory/memory_manager.py
- voice/offline_bridge.py
- core/event_bus.py
- actions/*.py

## 2. Runtime Layers
OMINI backend is organized as layered runtime responsibilities:

1. Session Orchestration Layer
- main.py (class OminiLive)
- Owns online/offline mode selection, Gemini Live session lifecycle, streaming audio loops, and tool call dispatch.

2. Action Execution Layer
- actions/*.py
- Stateless or lightly stateful operation modules for concrete capabilities:
  app launch, browser control, weather, reminders, files, screen process, system control, game updates, code/dev flows.

3. Agent Planning/Execution Layer
- agent/planner.py + agent/executor.py + agent/error_handler.py + agent/task_queue.py
- Used for multi-step tasks and autonomous workflows.

4. Memory Layer
- memory/memory_manager.py
- Local long-term memory persistence and prompt-context formatting.

5. Offline Voice Layer
- voice/offline_bridge.py
- Local STT/TTS and optional local LLM command routing when network is unavailable.

## 3. Boot and Lifecycle
Startup behavior (main.py):

1. UI is created on main thread.
2. Background thread starts assistant runtime.
3. Runtime waits for setup/API key readiness via UI gating.
4. OminiLive.run() enters connectivity-aware loop.

Key constants in main.py:
- LIVE_MODEL: models/gemini-2.5-flash-native-audio-preview-12-2025
- SEND_SAMPLE_RATE: 16000
- RECEIVE_SAMPLE_RATE: 24000
- CHUNK_SIZE: 1024

## 4. Online Path (Gemini Live)
When internet is available, runtime uses Gemini Live with native audio.

### 4.1 Session config
LiveConnectConfig includes:
- response modality: AUDIO
- transcript handling
- tool declarations (function schemas)
- system prompt + persona prompt + memory summary

### 4.2 Concurrent async loops
Online mode runs several concurrent loops:
- Mic capture loop
- Audio send loop
- Model response receive loop
- Speaker playback loop

Design implication:
- Full duplex voice experience with function-calling while preserving turn-level transcript logging.

### 4.3 Tool calls
When model emits function calls:
- Runtime dispatches each call to an explicit handler branch.
- Action return payload is sent back to model as function response.
- UI state is moved between LISTENING/THINKING/PROCESSING/SPEAKING around execution boundaries.

## 5. Offline Path
When internet is unavailable, runtime switches to offline bridge.

### 5.1 Connectivity checks
OfflineVoiceBridge.has_internet() uses:
- TCP probes to public endpoints
- HTTPS probes as fallback

### 5.2 STT backends
Selection order in _ensure_stt():
1. faster-whisper
2. openai-whisper
3. unavailable

### 5.3 Offline planning
plan_offline_turn() asks local Ollama model to emit strict JSON:
- mode: respond or tool
- tool_name + args for tool mode
- only allowed offline tool set is accepted

### 5.4 Offline-safe tool allow-list
Main runtime restricts offline tool execution to a safe subset (local-capable actions).
If unavailable/unsupported tool is requested, fallback is response-only behavior.

### 5.5 Local TTS
Piper executable is invoked with selected voice model, generated WAV is played through sounddevice.

## 6. Tool Contract and Dispatch
Tools are declared as function schemas in main.py (TOOL_DECLARATIONS) and dispatched via explicit branching.

Advantages:
- Predictable control flow.
- Easy tracing and logging.
- Explicit guardrails per tool.

Tradeoff:
- Central dispatch grows with tool count and needs maintenance discipline.

## 7. Agent Stack Internals
The agent package provides multi-step planning and autonomous execution.

### 7.1 planner.py
- Uses gemini-2.5-flash-lite with strict planning prompt.
- Returns JSON plan with bounded step count.
- Includes fallback plan when parsing/model output fails.

### 7.2 executor.py
- Executes plan steps via tool router.
- Supports context injection for file-writing flows.
- Includes translation helper for localized outputs.
- Has generated-code fallback path for hard tasks.

### 7.3 error_handler.py
- Classifies failure with ErrorDecision enum:
  retry, skip, replan, abort.
- Replan branch can generate alternate code-based attempt.

### 7.4 task_queue.py
- Priority queue with worker thread.
- Tracks task status lifecycle:
  pending, running, completed, failed, cancelled.
- Supports cancellation and completion callbacks.

## 8. Memory System
memory/memory_manager.py defines structured memory categories:
- identity
- preferences
- projects
- relationships
- wishes
- notes

Behavior details:
- Thread lock guards read/write.
- Entries carry value + updated date.
- Size trimming prevents unbounded growth.
- format_memory_for_prompt() converts stored entries into prompt-ready natural context.

## 9. Eventing and Background Systems
core/event_bus.py provides process-local pub/sub with:
- subscriber registry by event name
- wildcard subscribers
- internal queue for polling/consumption

Main runtime also wires additional agents/services (imported in main.py):
- system state monitor
- background scheduler
- event automation engine
- activity logger and replay
- safety layer

These modules enable continuous automation outside direct user turns.

## 10. Security and Safety Hooks
main.py imports and uses security helpers from security.py, including:
- tool authorization checks
- rate limits
- input/path sanitation and validation
- logging hooks

Operational recommendation:
- Keep all new action parameters validated before filesystem or shell operations.
- Reuse existing sanitize/validate helpers rather than adding ad hoc checks.

## 11. Data Files and Config
Key backend data/config files:
- config/api_keys.json
- core/prompt.txt
- memory/long_term.json
- logs/activity/*.jsonl

Persistence model:
- Local JSON files (no remote DB dependency by default).

## 12. Concurrency Model
Concurrency primitives used across backend:
- asyncio tasks for live voice streams
- daemon threads for background assistant runtime and queue workers
- thread locks around mutable shared state (memory, queue internals)

Design caveat:
- Cross-thread UI updates must stay signal-based via Qt signals (already done in ui.py).

## 13. Failure Modes and Recovery
Common failure classes:
- network disconnects
- tool action runtime errors
- malformed model JSON
- unavailable offline STT/TTS binaries

Recovery mechanisms:
- online/offline path switching
- planner fallback plan
- error decision model (retry/replan/abort)
- queue-based deferred execution

## 14. Extension Guide
To add a new backend capability safely:

1. Add action module in actions/ with clear parameter contract.
2. Add schema in TOOL_DECLARATIONS.
3. Add dispatch branch in main.py tool executor.
4. Optionally add planner awareness in agent/planner.py prompt.
5. Add validation/safety checks for any external side effects.
6. Add docs entry and at least one demo command.

## 15. Technical Debt Snapshot
Current notable debt/risk areas:
- Large centralized dispatch method in main.py (scale pressure).
- Planner prompt is long and tool list duplication risk exists.
- Mixed strategy between direct tool path and agent stack can diverge behavior.
- Generated-code fallback needs strict sandbox policy if expanded.

## 16. Backend Summary
Backend architecture is robust for a desktop AI assistant:
- clear orchestration core,
- broad tool ecosystem,
- resilient offline fallback,
- structured memory and recovery.

For long-term maintainability, prioritize modular dispatch decomposition, automated tests for tool schemas, and stronger failure-contract checks around external process calls.
