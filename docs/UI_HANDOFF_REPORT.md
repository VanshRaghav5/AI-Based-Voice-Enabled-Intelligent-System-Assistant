# UI Handoff Report for Another Copilot

## Goal of this report
This document describes the current UI system in this repository so another Copilot (in another codebase) can rebuild or adapt the same user experience and integration behavior.

It focuses on:
- visual structure and style
- runtime states and transitions
- input/output behavior
- threading and event flow
- integration contract between UI and assistant runtime
- implementation constraints and known issues

## Source files analyzed
- `ui.py` (primary UI implementation)
- `main.py` (runtime integration with UI)
- `actions/*.py` (UI logging usage from tools/actions)
- `requirements.txt` (UI-related dependencies)

## 1) UI architecture summary

### Framework and dependencies
- UI framework: Tkinter (`tkinter`)
- Image rendering: Pillow (`PIL.Image`, `ImageTk`, `ImageDraw`)
- Supporting libs: `threading`, `time`, `math`, `random`, `platform`, `collections.deque`
- Optional dependency referenced in dead code path: `numpy` (inside a branch that never executes)

### Main UI class
- Class: `OminiUI` in `ui.py`
- Construction entry point in `main.py`: `ui = OminiUI("face.png")`

### Window model
- Non-resizable centered window.
- Size clamps to screen:
  - `W = min(screen_width, 984)`
  - `H = min(screen_height, 816)`
- Uses custom full-canvas drawing loop plus separate widgets:
  - background animation canvas
  - log panel (`tk.Text`)
  - text input bar (`tk.Entry` + Send button)
  - mute toggle button (custom canvas)
  - optional setup modal (API key + OS selection)

## 2) Visual language and layout

### Theme direction
- High-contrast "Omini HUD" style.
- Dark black/cyan base with orange accent and red muted/error states.
- Monospace typography (`Courier`) used everywhere.

### Color palette constants
Defined in `ui.py` as constants:
- background: `#000000`
- primary cyan: `#00d4ff`
- mid cyan: `#007a99`
- dim cyan: `#003344`
- deep dim: `#001520`
- accent orange: `#ff6600`
- accent yellow: `#ffcc00`
- text cyan: `#8ffcff`
- panel: `#010c10`
- green: `#00ff88`
- red: `#ff3333`
- muted pink/red: `#ff3366`

### Screen regions
- Top header strip with:
  - system name
  - subtitle text
  - model badge
  - live clock
- Center area:
  - animated circular HUD rings, scan arcs, pulse rings
  - face image (masked circle) OR fallback orb when image unavailable
- Lower middle:
  - status line (LISTENING/THINKING/SPEAKING/etc.)
  - audio-style equalizer bars
- Bottom:
  - log panel
  - input bar
  - footer hint `[F4] MUTE`

### Log panel
- `tk.Text` in read-only mode except while typing.
- Tag colors:
  - `you` tag (light gray)
  - `ai` tag (primary cyan)
  - `sys` tag (yellow accent)
  - `err` tag (red)
- Typewriter-style output (character-by-character insertion).

## 3) Runtime states and behavior

### State machine values (UI-facing)
Set by `set_state(state: str)`:
- `MUTED`
- `SPEAKING`
- `THINKING`
- `LISTENING`
- `PROCESSING`
- fallback => `ONLINE`

### State effects
- `SPEAKING` drives stronger animation intensity:
  - faster ring spin
  - larger halo target
  - stronger pulse updates
- `MUTED` switches visuals to red/magenta style and blocks mic capture in runtime.
- `THINKING` and `PROCESSING` use blinking symbols in status text.
- status blinking toggles on a timer tick.

### Animation loop
- Loop function: `_animate()`
- Frame schedule: every 16 ms (`root.after(16, self._animate)`) (~60 FPS target)
- Randomized micro-variation for scale/halo to create organic movement.

## 4) Input/output behavior

### Keyboard and text command input
- Input box accepts Enter and keypad Enter.
- Send button triggers same submit handler.
- Submit flow:
  1. Trim text.
  2. Write `You: ...` to log.
  3. Call `on_text_command` callback in a daemon thread if callback is set.

### Voice and mute behavior
- F4 hotkey toggles mute.
- Mute button in UI also toggles mute.
- Mute toggle writes system log and updates state.

### Displaying assistant output
- Runtime writes transcriptions and tool/system logs with `write_log`.
- `write_log` enqueues messages and starts typewriter worker if idle.
- Message prefix controls tag and some state transitions:
  - `You:` => `PROCESSING`
  - `Omini:` or `AI:` => `SPEAKING`
  - errors/failures => `err` style

## 5) Setup/onboarding UI behavior

### First-run gate
- Checks `config/api_keys.json` for:
  - `gemini_api_key`
  - `os_system`
- If missing/invalid, shows setup frame and blocks runtime thread via `wait_for_api_key()` until saved.

### Setup fields and actions
- Hidden API key entry (`show="*"`)
- OS selector buttons for Windows/mac/Linux (auto-detect preselect)
- Save action writes JSON to `config/api_keys.json` and unlocks runtime.

## 6) Integration contract (important for porting)

Another codebase that wants the same behavior should preserve this interface contract.

### Required UI object surface used by runtime/actions
Runtime in `main.py` and actions assume the UI object exposes:
- attribute: `muted` (bool)
- attribute: `on_text_command` (callable or None)
- method: `set_state(state: str)`
- method: `write_log(text: str)`
- method: `wait_for_api_key()`
- property: `root` with `mainloop()` available

### Runtime -> UI interactions in `main.py`
- binds text callback: `self.ui.on_text_command = self._on_text_command`
- writes online/system logs
- sets state transitions around:
  - tool execution start/end
  - connection/reconnection
  - speaking/listening
- mic input capture condition depends on `not self.ui.muted`
- transcription outputs are written as:
  - `You: {full_in}`
  - `Omini: {full_out}`

### Actions -> UI interactions
Most actions only need:
- `player.write_log(...)`
No action currently depends on advanced UI methods like `start_speaking`/`stop_speaking`.

## 7) Concurrency and event model

### Threading model
- Tkinter main thread owns UI rendering and widgets.
- Assistant runtime (`OminiLive`) runs in separate daemon thread using `asyncio.run(...)`.
- Text submit callback dispatches command send in another daemon thread.

### Potential thread-safety caveat
- `write_log` is called from non-UI contexts (runtime/action threads).
- Tkinter is not fully thread-safe by design.
- Current code appears to work in practice, but a stricter implementation should marshal UI updates to the Tk thread (for example via `root.after(0, ...)` queue dispatch).

## 8) Functional behavior checklist for reimplementation

If another project rebuilds this UI, it should implement all of the following:

1. Non-resizable centered window with screen clamp (max 984x816).
2. Full-canvas animated HUD look with ring/scan/pulse behavior.
3. Distinct visual mode for muted state (color + status semantics).
4. Log panel with typewriter animation and semantic tag colors.
5. Text command input + Send button + Enter shortcuts.
6. Mute toggle via both UI button and F4 hotkey.
7. State machine semantics for LISTENING/THINKING/PROCESSING/SPEAKING/MUTED.
8. First-run setup modal with API key and OS selection persisted to JSON.
9. Public UI API compatible with runtime/action usage (see contract above).
10. Runtime wiring that logs both user transcript and assistant transcript lines.

## 9) Known issues / quirks worth preserving or improving

### Preserve if exact clone is desired
- Hard exit on window close uses `os._exit(0)`.
- Typewriter speed and randomized animation produce current personality/look.

### Improve if modernizing
- Replace hard exit with graceful shutdown hooks.
- Enforce Tk thread-safe log updates using event queue.
- Remove dead code branch in `_draw` around muted image tint (`if False`).
- Consider fallback font strategy (Courier may vary by platform).
- Optional: improve high-DPI behavior and accessibility controls.

## 10) Ready-to-paste prompt for another Copilot

Use the following prompt in the target repository:

```text
I want you to implement a desktop UI that matches the OMINI behavior and integration contract.

Build a Tkinter-based assistant UI with:
- Non-resizable centered window, max size 984x816.
- Cyber HUD style: black background, cyan primary, orange/yellow accents, red muted/error state.
- Main animated canvas with circular rings, scan arcs, pulses, and either circular face image or fallback glowing orb.
- Header with system title, subtitle, model badge, live clock.
- Status line showing LISTENING/THINKING/PROCESSING/SPEAKING/MUTED with blink effects.
- Equalizer-style bars that animate differently when speaking/muted/idle.
- Log panel with typewriter output and tags: you, ai, sys, err.
- Input entry + SEND button; Enter submits text command.
- Mute toggle button and F4 hotkey.
- First-run setup modal if config keys missing: ask Gemini API key + OS selection, save to config/api_keys.json.

Expose this exact UI integration surface for runtime/tools:
- ui.muted: bool
- ui.on_text_command: callable or None
- ui.set_state(state: str)
- ui.write_log(text: str)
- ui.wait_for_api_key()
- ui.root.mainloop()

Behavior requirements:
- write_log("You: ...") should put UI in PROCESSING state.
- write_log("Omini: ...") should put UI in SPEAKING state.
- When idle and not muted, state should return to LISTENING.
- Runtime must be able to gate microphone capture based on ui.muted.
- Keep animation loop near 60 FPS with root.after(16, ...).

Engineering constraints:
- Keep UI updates thread-safe (marshal non-UI thread log/state updates to Tk main thread).
- Keep the look and feel close to OMINI while making code cleaner and modular.

Deliverables:
1) ui module/class implementation
2) minimal runtime wiring example showing transcript in/out and state transitions
3) config setup flow for API key + OS
4) short README section explaining controls and states
```

## 11) Fast validation checklist

After implementation in the target project, verify:
- App launches and animates smoothly.
- F4 toggles mute and status/colors update instantly.
- Enter in input box logs `You: ...` and triggers command callback.
- Runtime can push `Omini: ...` lines and they appear with typewriter effect.
- Missing config opens setup modal and blocks runtime until saved.
- Runtime can read `ui.muted` and suppress mic capture.
- No Tkinter thread exceptions during heavy action logging.

