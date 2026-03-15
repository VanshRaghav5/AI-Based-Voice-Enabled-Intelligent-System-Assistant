# Wake Word Feature - User Guide

## 🎙️ Wake Word Detection

Your voice assistant now supports **wake word detection**! Say "**Omini**" and the assistant will automatically start listening without needing to click the button.

---

## 📋 How to Use

### 1. **Enable Wake Word Detection**

Click the **"💤 Wake Word: OFF"** button in the chat window. It will turn green and show **"👂 Wake Word: ON"**.

### 2. **Say the Wake Word**

Simply say one of these wake words:
- **"Omini"**
- **"Hey Omini"**
- **"OK Omini"**

The assistant will automatically:
- ✅ Detect the wake word
- ✅ Start listening for your command
- ✅ Show the listening overlay
- ✅ Process your request

### 3. **Give Your Command**

After saying the wake word, immediately speak your command:
- *"Omini, send email to test@example.com"*
- *"Hey Omini, open Chrome"*
- *"OK Omini, what's the weather?"*

### 4. **Disable Wake Word**

Click the **"👂 Wake Word: ON"** button to turn it off. It will return to **"💤 Wake Word: OFF"**.

---

## ⚙️ Configuration

Wake word settings are in `backend/config/assistant_config.json`:

```json
{
  "wake_word": {
    "enabled": false,
    "words": ["omini", "hey omini", "ok omini"],
    "listen_duration": 1.5,
    "sensitivity": "medium"
  }
}
```

**Settings:**
- `enabled` - Auto-start wake word detection on backend startup
- `words` - List of wake words to detect (case-insensitive)
- `listen_duration` - How long to record each check (shorter = faster response)
- `sensitivity` - Detection sensitivity (not yet implemented)

---

## 🔧 How It Works

1. **Continuous Monitoring**: When enabled, the system records short 1.5-second audio clips continuously
2. **Speech Recognition**: Each clip is transcribed using Whisper STT
3. **Wake Word Match**: If any wake word is detected, voice listening activates automatically
4. **Auto-Pause**: Wake word detection pauses during active listening to avoid conflicts
5. **Auto-Resume**: After your command is processed, wake word detection resumes

---

## 💡 Tips

- **Speak clearly** when saying the wake word
- **Wait briefly** (~0.5s) after the wake word before your command
- Wake word detection uses your **microphone continuously** (minimal CPU impact)
- If wake word isn't detected, try speaking **louder** or **closer to mic**
- The wake word is **case-insensitive** - "OMINI", "omini", "Omini" all work

---

## ⚠️ Important Notes

- Wake word detection requires an **active microphone**
- Backend must be **running** for wake word to work
- If detection is slow, check `listen_duration` in config (lower = faster but less accurate)
- Wake word automatically **pauses** during:
  - Active voice listening
  - TTS playback
  - Command processing

---

## 🐛 Troubleshooting

**Wake word not detected:**
- ✅ Check microphone is working (see [MICROPHONE_SETUP_GUIDE.md](MICROPHONE_SETUP_GUIDE.md))
- ✅ Ensure wake word detection button shows **"👂 Wake Word: ON"**
- ✅ Speak **clearly** and **loudly**
- ✅ Check backend logs for `[WakeWord] ✓ DETECTED` messages

**Detection too slow:**
- Reduce `listen_duration` from 1.5 to 1.0 in config
- Restart backend after changing config

**False triggers:**
- Add more specific wake words (e.g., "hey otto assistant" instead of just "otto")
- Increase `listen_duration` for better accuracy

---

## 🎯 Example Usage

```
User: "Otto"
Assistant: 👂 'otto' detected! Listening...
User: "Send email to john@example.com saying hello"
Assistant: ✅ Completed sir
[Wake word detection automatically resumes]
```

---

**Enjoy hands-free control of your assistant! 🚀**
