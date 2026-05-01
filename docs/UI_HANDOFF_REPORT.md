# UI Handoff Report (PySide6)

## Goal
This document is for engineers or another Copilot instance who need to rebuild, extend, or port the current OMINI UI behavior.
It reflects the current implementation in ui.py (PySide6), not the legacy Tkinter design.

## Source of truth
- ui.py
- main.py (UI integration calls)

## 1. Frontend architecture summary

### Framework and runtime
- UI framework: PySide6 (Qt Widgets)
- Render model: custom QPainter drawing in paintEvent methods
- Animation model: timer-driven at roughly 60 FPS (16 ms QTimer)

### Main classes
- LoginScreen: themed login/register/guest auth surface.
- CentralOrbWidget: central animated interactive orb (eye/reactor/orb modes).
- WaveformWidget: speaking/muted waveform bars.
- OminiUI: main application shell, controls, logs, status, and theme switching.

## 2. Visual structure

### Window and layout
- Fixed-size desktop window (bounded by screen size).
- Major zones:
  - Header strip with system title/time metadata.
  - Center orb interaction area.
  - Status + waveform band.
  - Log panel and input row.
  - Footer controls and right-side HUD panel.

### Theme system
Theme definitions are centralized in THEMES and currently include:
- amethyst
- hogwarts
- avengers

Each theme includes color tokens, typography, orb_mode defaults, and accent RGB values.

## 3. Interaction behavior

### Orb interactions
- Left click: interaction pulse + click signal.
- Right click: context menu path for mode/theme interactions.
- Hover: emits hover_changed and can show contextual tooltip.
- Mouse wheel: adjusts animation intensity within bounds.

### Global controls
- Text command input and SEND button.
- Mute/live toggle.
- Theme buttons.
- Keyboard shortcuts:
  - F4: mute toggle
  - F5: cycle theme
  - F11: fullscreen

## 4. State model and visual mapping
UI-facing states:
- LISTENING
- THINKING
- PROCESSING
- SPEAKING
- MUTED

Effects:
- Orb scale/halo/animation parameters shift by state.
- Waveform responds to speaking/mute.
- Status row and HUD indicators reflect state transitions.

## 5. Backend integration contract
Runtime code expects UI object methods/attributes:
- muted (bool)
- on_text_command (callable)
- write_log(text)
- set_state(state)
- wait_for_api_key()
- run()

Signal-based thread-safe channels in OminiUI:
- log_requested
- state_requested

These signals are important because backend orchestration runs outside the UI thread.

## 6. Rendering pipeline notes

### OminiUI.paintEvent responsibilities
- Window background and ambient gradients
- Vignette and scanline overlays
- Background particles and data glyphs
- Header/footer/status/hud draw calls
- Theme-specific overlays

### CentralOrbWidget.paintEvent responsibilities
- Orb mode selection
- Eye/reactor/orb layered visuals
- Pulses, particles, ring elements
- Hover/click feedback

### Alpha safety
safe_set_alpha helper clamps alpha values before applying to QColor.
This prevents invalid alpha warnings and keeps rendering stable under dynamic math.

## 7. Setup flow
First run behavior:
- UI checks API key configuration readiness.
- If missing, setup UI path is shown.
- Backend startup waits for setup completion.

## 8. Known engineering constraints
- ui.py is large and combines visual, interaction, and state orchestration.
- Any paint/math refactor should preserve alpha clamping and per-frame cost limits.
- DPI behavior can vary by Windows privileges/environment.

## 9. Porting checklist
When porting this UI to another project, preserve:
1. PySide6 signal-safe update pattern.
2. State names and semantics used by backend.
3. Orb interaction contract (left/right click, hover, wheel).
4. Theme token structure and runtime switching behavior.
5. Fixed animation cadence with bounded particle lifetimes.

## 10. Prompt for another Copilot
Use this in a target project when recreating the interface:

Build a PySide6 desktop assistant UI with:
- animated central orb widget supporting eye/reactor/orb modes,
- multi-theme visual system (amethyst/hogwarts/avengers style),
- fixed-size HUD layout with header, log panel, waveform, input row, and right-side stats,
- Qt signal-safe methods for write_log and set_state from backend threads,
- F4 mute, F5 theme cycle, F11 fullscreen,
- right-click orb context controls and hover tooltip,
- robust alpha clamping for all QColor alpha writes.
