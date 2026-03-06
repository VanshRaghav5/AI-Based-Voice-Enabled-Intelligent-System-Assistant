# OmniAssist AI - Voice Assistant

AI-powered voice assistant with desktop interface.

## Quick Start

### For Users (Simple)
```
Double-click: START.bat
```
That's it! The app launches automatically.

### For Developers (Debug Mode)
```
Double-click: launcher.bat
```
Shows detailed logs and status messages.

---

## First Time Setup

### 1. Install Ollama
Download from: https://ollama.ai

### 2. Download AI Model
```powershell
ollama pull qwen2.5:7b-instruct-q4_0
```

### 3. Setup Python Environment
```powershell
python -m venv venv
.\venv\Scripts\pip install -r backend/requirements.txt
.\venv\Scripts\pip install -r desktop_1/requirements.txt
```

### 4. Launch
```
Double-click START.bat
```

---

## What Each Launcher Does

**START.bat** - Simple launcher
- Starts backend in background
- Opens desktop app
- Minimal output
- Best for regular use

**launcher.bat** - Debug launcher
- Shows all logs
- Checks Ollama status
- Displays errors
- Best for troubleshooting

---

## Voice Commands

Try saying:
- "Open YouTube"
- "Open WhatsApp"
- "Search Google for..."
- "Send message"

Or type commands instead of speaking.

---

## Troubleshooting

### Backend won't start
```powershell
# Check logs
type logs\backend.log

# Manual start to see errors
.\venv\Scripts\python.exe backend\api_service.py
```

### Ollama not running
```powershell
# Start Ollama
ollama serve

# In another terminal
ollama ps
```

### Dependencies missing
```powershell
.\venv\Scripts\pip install -r backend/requirements.txt
.\venv\Scripts\pip install -r desktop_1/requirements.txt
```

---

## System Requirements

- Windows 10+
- 8GB RAM (16GB recommended)
- RTX 3050 or better GPU
- 5GB disk space
- Ollama installed

---

## Performance

- First launch: 15-30 seconds (model loading)
- Subsequent launches: 5-10 seconds
- Request response: 2-4 seconds

---

## Stopping the App

- Close the desktop window
- Close the launcher console (Ctrl+C or close window)

---

For more details, see the documentation in `docs/` folder.
