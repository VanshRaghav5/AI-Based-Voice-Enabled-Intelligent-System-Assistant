# OmniAssist AI — Desktop Client

The desktop front-end for OmniAssist AI. Built with **CustomTkinter**, it provides JWT-authenticated access, a modern chat interface with message bubbles, a Siri-style voice overlay, and real-time Socket.IO communication with the backend.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r desktop_1/requirements.txt

# 2. Start the backend (separate terminal)
python backend/api_service.py

# 3. Launch the desktop client
python desktop_1/main.py
```

> Backend must be running on `http://127.0.0.1:5000` before launching the client.

---

## Features

| Area | Details |
|------|---------|
| **Authentication** | Login, registration, JWT token persistence (`~/.omniassist/token.json`), auto-verify on startup, logout |
| **Chat UI** | Message bubbles with avatars (👤 user / 🤖 assistant), system alerts, welcome message, auto-scroll |
| **Voice Input** | Fullscreen Siri-style overlay, audio-reactive orb, live transcription, push-to-listen |
| **Settings** | Theme (dark/light), persona, language, memory toggle, font size — persisted to `~/.omniassist/ui_settings.json` |
| **Real-Time** | Socket.IO events for transcription, execution steps, confirmations, errors |
| **Thread Safety** | All socket callbacks routed through `_safe_ui_update()` to avoid cross-thread Tkinter crashes |

---

## Application Flow

```
Launch → Token Check
           │
     ┌─────┴─────┐
  Valid Token   No Token
     │              │
  Main App      Login Window ⇄ Register Window
     │              │
  Chat Window   On Success → Main App
     │
  Logout → Login Window
```

---

## Project Structure

```
desktop_1/
├── main.py                  # App controller — auth flow, window lifecycle
├── config.py                # App-level configuration
├── settings_manager.py      # Persistent UI settings (~/.omniassist/)
├── requirements.txt         # Python dependencies
│
├── ui/
│   ├── chat_window.py       # Chat interface — messages, input, voice, logout
│   ├── login_window.py      # JWT login form
│   ├── register_window.py   # User registration form
│   ├── settings_modal.py    # Settings dialog (theme, persona, language)
│   ├── listening_overlay.py # Fullscreen voice overlay
│   ├── siri_orb.py          # Audio-reactive orb animation
│   ├── status_bar.py        # Connection & state indicators
│   └── confirmation_popup.py# Safety confirmation dialogs
│
├── audio/
│   └── mic_visualizer.py    # Microphone amplitude capture (~30 FPS)
│
└── services/
    ├── api_client.py        # REST client — auth, commands, settings
    └── socket_client.py     # Socket.IO client — real-time events
```

---

## Backend Integration

### REST Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login` | POST | Authenticate user |
| `/api/auth/register` | POST | Create account |
| `/api/auth/verify` | POST | Validate stored JWT |
| `/api/auth/logout` | POST | Invalidate session |
| `/api/process_command` | POST | Execute a text command |
| `/api/start_listening` | POST | Activate voice capture |
| `/api/stop_listening` | POST | Deactivate voice capture |
| `/api/confirm` | POST | Approve/deny pending action |
| `/api/settings` | GET/PUT | Read/update assistant settings |

### Socket.IO Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `voice_input` | Server → Client | Live speech transcription |
| `command_result` | Server → Client | Execution result |
| `execution_step` | Server → Client | Multi-step progress update |
| `confirmation_required` | Server → Client | Safety confirmation prompt |
| `listening_status` | Server → Client | Mic state change |
| `error` | Server → Client | Error notification |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern themed Tkinter UI |
| `requests` | HTTP client for REST API |
| `python-socketio` | Real-time WebSocket communication |
| `websocket-client` | WebSocket transport layer |
| `pyaudio` | Microphone audio capture |
| `numpy` | Audio amplitude processing |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Login window not appearing | Ensure backend is running; check `http://localhost:5000/api/health` |
| "Connection refused" errors | Start backend first: `python backend/api_service.py` |
| Microphone not detected | Verify PyAudio: `python -c "import pyaudio; print('OK')"` |
| UI crashes on socket event | Update to latest codebase — thread-safety wrappers required |
| Settings not saving | Check write permissions to `~/.omniassist/` |

---

## Local Storage

All user data is stored locally under `~/.omniassist/`:

| File | Contents |
|------|----------|
| `token.json` | JWT token + user info (auto-loaded on startup) |
| `ui_settings.json` | Theme, persona, language, font size preferences |
