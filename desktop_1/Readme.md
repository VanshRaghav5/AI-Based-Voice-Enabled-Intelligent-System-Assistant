# OmniAssist AI - Desktop UI

Modern desktop interface for the OmniAssist AI voice assistant, built with CustomTkinter.

## 📁 Project Structure

```
desktop_1/
├── main.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── ui/
│   ├── chat_window.py     # Main chat interface with bubbles
│   ├── status_bar.py      # Real-time status indicators
│   └── confirmation_popup.py  # Confirmation dialogs
└── services/
    ├── api_client.py      # REST API client
    └── socket_client.py   # WebSocket client
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `customtkinter` - Modern UI framework
- `requests` - HTTP client
- `python-socketio[client]` - WebSocket support

### 2. Start Backend Server

```bash
# From project root
python backend\api_service.py
```

Backend runs on `http://localhost:5000`

### 3. Launch Desktop UI

```bash
# From project root
python desktop_1\main.py
```

## ✨ Features

### 💬 Chat Interface
- **Message Bubbles**: User (blue, right) / Assistant (green, left) / System (orange, center)
- **Processing Indicator**: Purple "thinking" bubble while processing
- **Multi-Step Execution**: Live step-by-step progress display
- **Auto-scroll**: Always shows latest messages

### 🎤 Voice Control
- **Start/Stop Listening**: Toggle microphone with visual feedback
- **Live Transcription**: See what you say in real-time
- **Voice Input Events**: Shows "🎤 Heard: ..." messages

### 📊 Status Bar
Real-time indicators at bottom:
- 🟢 **Connected** / 🔴 **Disconnected**
- 🎤 **Listening...** (when mic active)
- ⚙ **Processing...** (during command execution)

### ⚙️ Settings Indicator
Top-right badge showing:
- 💾 **Memory**: ON/OFF - Conversation memory status
- 🎭 **Persona**: Friendly/Professional/Concise
- 🌐 **Language**: English/Hindi/Hinglish

### 🔄 Real-Time Updates (WebSocket)
- `voice_input` - Live speech transcription
- `command_result` - Command execution results
- `execution_step` - Multi-step progress (🔹 running, ✅ success, ❌ failed)
- `confirmation_required` - Safety confirmations for critical actions
- `error` - Error notifications

### 🛡️ Smart Error Handling
- **Connection Retry**: Auto-retry on backend disconnect
- **30s Timeout**: Re-enables input if no response
- **Threading**: Non-blocking UI during command processing
- **Auto-focus**: Input field ready after each command

## 🎨 UI Components

### ChatWindow (`ui/chat_window.py`)
Main interface with:
- Scrollable message area
- Input field with Enter-key support
- Send button (disabled during processing)
- Start/Stop Listening button
- Memory/Settings indicator

### StatusBar (`ui/status_bar.py`)
Bottom bar showing:
- Connection status (green/red)
- Listening status (blue)
- Processing status (orange)

### ConfirmationPopup (`ui/confirmation_popup.py`)
Dialog for critical actions like:
- System shutdown
- File deletion
- Risky operations

## 🔧 API Integration

### REST Endpoints Used
- `POST /api/process_command` - Send text commands
- `POST /api/start_listening` - Enable microphone
- `POST /api/stop_listening` - Disable microphone
- `POST /api/confirm` - Approve/deny confirmations

### WebSocket Events
**Received:**
- `connection_status` - Initial connection state
- `voice_input` - Speech transcription
- `command_result` - Execution results
- `execution_step` - Step progress
- `confirmation_required` - Confirmation requests
- `listening_status` - Mic state changes
- `error` - Error messages

**Sent:**
- `send_command` - Alternative to REST API

## 💡 Usage Examples

### Text Commands
1. Type command in input field
2. Press Enter or click Send
3. Watch step-by-step execution
4. Get assistant response

### Voice Commands
1. Click "Start Listening"
2. Speak your command
3. See live transcription
4. Automatic processing

### Example Commands
- "open WhatsApp"
- "search for weather on Google"
- "lock my computer"
- "send message to [contact] saying [message]"

## 🎯 Key Highlights

✅ **Production-Ready UI** - Polished chat bubbles, not terminal output  
✅ **Real-Time Feedback** - Live status, processing, and step indicators  
✅ **Async Processing** - Non-blocking UI with timeout protection  
✅ **Professional UX** - Clawbot-level polish and responsiveness  
✅ **Smart Error Handling** - Graceful degradation on connection issues  

## 📝 Configuration

Edit `config.py` to customize:
- Backend URL (default: `http://127.0.0.1:5000`)
- UI theme (dark/light)
- Default settings

## 🐛 Troubleshooting

**UI shows "Backend not running":**
- Ensure `backend\api_service.py` is running
- Check backend is on `http://localhost:5000`

**Input field stuck disabled:**
- Fixed with 30s timeout auto-reset
- Check browser console for errors
- Restart UI if needed

**WebSocket disconnects repeatedly:**
- Backend may be overloaded
- Check backend terminal for errors
- Verify no firewall blocking port 5000

## 🚧 Future Enhancements

- [ ] Settings panel (toggle memory, persona, language)
- [ ] Chat history export
- [ ] Custom themes
- [ ] Keyboard shortcuts
- [ ] Notification sounds
- [ ] System tray integration

---

**Built with** ❤️ **for the Indian AI ecosystem**
