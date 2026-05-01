# OMINI Frontend Deep Technical Understanding

## 1. Scope
This document explains the frontend/UI architecture, rendering pipeline, interactions, theming system, and runtime integration contract used by OMINI.

Primary source module:
- ui.py (PySide6)

## 2. Frontend Stack
UI framework and rendering stack:
- PySide6 (Qt Widgets)
- Custom paint rendering via QPainter
- Timer-driven animation (16 ms tick)
- Qt signal/slot for thread-safe backend-to-UI updates

This is not a declarative UI; it is an imperative, custom-painted, animation-heavy widget hierarchy.

## 3. UI Class Topology
Main classes in ui.py:

1. LoginScreen (QtWidgets.QWidget)
- Authentication/identity entry screen with themed styling.

2. CentralOrbWidget (QtWidgets.QWidget)
- Core animated center visual.
- Supports multiple rendering modes:
  eye, reactor, orb.
- Emits clicked, right_clicked, and hover_changed signals.

3. WaveformWidget (QtWidgets.QWidget)
- Animated audio-reactive bars linked to speaking/muted state.

4. OminiUI (QtWidgets.QWidget)
- Main shell window.
- Composes orb, logs, controls, waveform, theme buttons, and HUD.

## 4. Theme System
Theme data is centralized in THEMES dict.
Each theme defines:
- semantic color tokens (bg, panel, primary, dim, accent, etc.)
- typography choices
- orb rendering hints (orb_mode, ring_style)
- state RGB sets (speak/listen/think/mute)

Current themes:
- amethyst
- hogwarts
- avengers

Global theme accessor:
- T() returns current active theme map.

## 5. Render Architecture
Rendering is split between:

1. Widget-local painting
- CentralOrbWidget.paintEvent() handles detailed center visual stack.
- WaveformWidget.paintEvent() handles audio bars.

2. Shell painting
- OminiUI.paintEvent() draws full-window background effects:
  gradient atmosphere, vignette, grid/circuit/stars, header/footer, HUD overlays.

### 5.1 Paint layering strategy
Typical shell paint order:
1. Background fill
2. Ambient glow
3. Vignette
4. Particles
5. Grid/scan overlays
6. Data glyphs
7. Header/footer/status/HUD
8. Theme-specific overlays

### 5.2 Orb mode strategy
Central orb has specialized sub-painters:
- Eye mode (biomechanical eye)
- Reactor mode (arc-reactor inspired ring geometry)
- Generic orb mode

Each mode has independent state variables for believable motion.

## 6. Animation Engine
Animation heartbeat:
- OminiUI._anim_timer triggers _animate() every ~16 ms.

State evolution includes:
- global phases for glow/scan/vignette pulses
- background particle spawn/decay
- orbiting character streams
- waveform smoothing
- orb internal tick state machine

This produces deterministic real-time updates with controlled random perturbations for organic feel.

## 7. Interaction Model
User interactions are event-driven:

- Left click on orb:
  triggers energy pulse, flash, and click signal.

- Right click on orb:
  opens orb context actions (theme/mode interaction path).

- Hover on orb:
  hover_changed signal and tooltip visibility management.

- Mouse wheel over orb:
  modifies global animation intensity within bounds.

- Keyboard shortcuts:
  F4 mute toggle
  F5 theme cycle
  F11 fullscreen toggle

## 8. Input, Logs, and Status UX
Main operator controls in OminiUI:
- command input field
- send button
- mute/live button
- theme buttons
- persona/voice/live-voice selectors
- log panel (QTextEdit)

Status behavior:
- logical states: LISTENING, THINKING, PROCESSING, SPEAKING, MUTED
- status row and orb visuals react to state transitions
- waveform reacts to speaking/mute flags

## 9. Integration Contract With Backend
Backend expects OminiUI to expose and support:
- muted boolean
- on_text_command callback
- write_log(text)
- set_state(state)
- wait_for_api_key()
- run()/event loop ownership

Thread-safe update pathway:
- log_requested signal
- state_requested signal

These signals ensure backend/runtime threads do not mutate Qt widgets directly.

## 10. Setup and First-Run Flow
UI checks config readiness on startup:
- API key exists and is validly structured
- if missing, setup UI is shown and runtime waits for completion

This gating prevents backend session startup with incomplete credentials.

## 11. Technical Rendering Notes
- WA_TranslucentBackground used for layered visual blending in key widgets.
- Extensive antialiasing enabled for painter quality.
- Alpha compositing is heavily used for glow and depth.
- safe_set_alpha helper clamps all alpha values to avoid Qt warnings and invalid channels.

## 12. Performance Characteristics
Cost drivers:
- high-frequency full-window paint operations
- per-frame particle and glyph loops
- multiple gradients and radial effects

Mitigations already present:
- bounded lists and decay/removal for particles/rings
- moderate geometry complexity for repeated primitives
- single global animation timer

Potential future optimizations:
- cache static geometry per theme
- reduce random-heavy loops at low-power mode
- introduce quality tiers tied to animation intensity

## 13. Frontend Extension Guide
To add a new visual theme safely:

1. Add theme entry in THEMES with complete token set.
2. Provide orb_mode and ring_style defaults.
3. Ensure text contrast is readable in log/input/HUD components.
4. Validate all painter alpha writes via safe_set_alpha.
5. Add selector button styling path in OminiUI._style_theme_btn.

To add a new orb mode:

1. Add mode selector plumbing and set_orb_mode mapping.
2. Create dedicated painter branch in CentralOrbWidget.
3. Add tick-state variables and lifecycle updates.
4. Keep per-frame object churn low.

## 14. Known Frontend Risks
- ui.py is large and multi-responsibility; difficult to test in isolation.
- Rich custom painting raises regression risk when changing alpha/math logic.
- DPI handling may vary across Windows privilege contexts.

## 15. Frontend Summary
The frontend is a custom-rendered PySide6 visual system with advanced animation and strong thematic identity.
Its architecture is suitable for immersive assistant experiences, with clean backend integration through Qt signals and explicit UI state channels.
