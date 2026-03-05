# OmniAssist AI - Desktop Interface

Voice-enabled AI assistant with Siri-style fullscreen overlay and real-time audio visualization.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Backend
```bash
python backend/api_service.py
```
Backend runs on `http://127.0.0.1:5000`

### 3. Launch Desktop UI
```bash
python desktop_1/main.py
```

## ✨ Key Features

### 🎙️ Siri-Style Voice Interface
- **Fullscreen Overlay** - Immersive voice interaction experience
- **Audio-Reactive Orb** - Glowing orb that responds to voice amplitude
- **Live Transcription** - Real-time speech-to-text display
- **Smooth Animations** - Fade transitions and breathing effects

### 💬 Modern Chat Interface
- **Message Bubbles** - User (blue) / Assistant (gray) / System (orange)
- **Typewriter Effect** - Animated assistant responses
- **Execution Steps** - Live progress indicators for multi-step tasks
- **Auto-scroll** - Always shows latest messages

### 📊 Smart Status Indicators
- 🟢/🔴 **Connection Status** - Backend connectivity
- 🎤 **Listening** - Active voice capture
- ⚙️ **Processing** - Command execution
- 💾 **Memory** / 🎭 **Persona** / 🌐 **Language** - Current settings

### 🎨 Audio Visualization
- **Real-Time Amplitude** - Microphone input visualization (~30 FPS)
- **Smooth Interpolation** - Fluid orb size transitions
- **Background Processing** - Non-blocking audio capture

## 📁 Project Structure

```
desktop_1/
├── main.py                      # Application entry point
├── requirements.txt             # Dependencies
│
├── ui/
│   ├── chat_window.py          # Main chat interface
│   ├── listening_overlay.py    # Fullscreen Siri overlay
│   ├── siri_orb.py            # Audio-reactive orb visualizer
│   ├── status_bar.py          # Status indicators
│   └── confirmation_popup.py   # Confirmation dialogs
│
├── audio/
│   └── mic_visualizer.py      # Microphone amplitude capture
│
└── services/
    ├── api_client.py          # REST API client
    └── socket_client.py       # Socket.IO WebSocket client
```

## 🎯 Usage

### Text Commands
1. Type command in input field
2. Press **Enter** or click **Send**
3. Watch real-time execution steps
4. Get assistant response with typewriter animation

### Voice Commands
1. Click **🎙 Start Listening**
2. **Fullscreen overlay appears** with glowing orb
3. **Speak** your command - orb reacts to your voice
4. Watch **live transcript** update
5. Overlay transitions to **"Processing..."** state
6. Assistant responds and overlay **fades out**

## 🔧 State Transitions

```
IDLE → Click "Start Listening" → LISTENING
  (Overlay shows, orb reacts to voice)
       ↓ 
   Voice input complete
       ↓
PROCESSING (Orb slow pulse, "Processing..." text)
       ↓
   Backend responds
       ↓
RESPONDING (Fade out, result in chat)
       ↓
    IDLE
```

## 🔌 Backend Integration

### REST Endpoints
- `POST /api/process_command` - Submit text command
- `POST /api/start_listening` - Activate microphone
- `POST /api/stop_listening` - Deactivate microphone
- `POST /api/confirm` - Approve/deny confirmations

### Socket.IO Events
| Event | Purpose |
|-------|---------|
| `voice_input` | Live speech transcription |
| `command_result` | Execution results |
| `execution_step` | Multi-step progress |
| `confirmation_required` | Safety confirmations |
| `listening_status` | Mic state changes |
| `error` | Error messages |

## 🐛 Troubleshooting

**Backend not connecting:**
- Ensure backend is running: `python backend/api_service.py`
- Verify backend URL: `http://127.0.0.1:5000`
- Check firewall settings

**Microphone not working:**
- Verify PyAudio installation: `python -c "import pyaudio; print('OK')"`
- Check system microphone permissions
- Test with another audio app

**Overlay not showing:**
- Check console for errors
- Verify CustomTkinter version: `pip show customtkinter`
- Restart application

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern UI framework |
| `requests` | HTTP client |
| `python-socketio` | WebSocket communication |
| `pyaudio` | Microphone audio capture |
| `numpy` | Audio amplitude calculation |

## 💡 Example Commands

- `"open YouTube"`
- `"search for AI tutorials on Google"`
- `"send WhatsApp message to John saying hello"`
- `"lock my computer"`
- `"play music"`

---

**Built with ❤️ using CustomTkinter, PyAudio, and NumPy**
