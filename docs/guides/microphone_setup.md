# Microphone Setup Guide

## Issue: Voice listening not working

Your voice assistant is configured correctly, but the microphone is not capturing audio.

### Quick Diagnostics Result

```
Audio RMS Level: 1 (Threshold: 200)
Status: SILENT - No audio detected
```

This means the microphone is either:
- Not connected
- Muted or volume too low  
- Wrong device selected as default
- Permissions not granted

---

## ✅ Steps to Fix

### 1. Check Windows Microphone Settings

**Option A: Quick Access**
1. Right-click the **Speaker icon** in taskbar (bottom-right)
2. Click **"Sound settings"** or **"Open Sound settings"**
3. Scroll down to **Input** section
4. Click **"Choose your input device"** dropdown
5. Select your active microphone (e.g., "Microphone Array", "Headset")
6. Speak into the microphone and watch the blue bar under **"Test your microphone"**
   - If the bar moves, your mic works!
   - If it doesn't move, try the next step

**Option B: Control Panel**
1. Press `Win + R`, type `mmsys.cpl`, press Enter
2. Go to **Recording** tab
3. Find your microphone and right-click → **Set as Default Device**
4. Right-click again → **Properties**
5. Go to **Levels** tab → Make sure volume is at **80-100%** and not muted
6. Click **OK** to save

### 2. Check Application Permissions

1. Press `Win + I` to open **Settings**
2. Go to **Privacy & Security** → **Microphone**
3. Make sure **"Microphone access"** is **ON**
4. Scroll down and enable for **Python** or **Desktop apps**

### 3. Test Microphone in Windows

1. Press `Win + S` and search for **"Voice Recorder"**
2. Open the app and click the **Record** button
3. Speak for a few seconds
4. Stop recording and play it back
5. If you hear your voice → Microphone works!

### 4. Available Microphones on Your System

From the diagnostic, these microphones are available:
- **Microphone Array (AMD Audio Device)** - Built-in laptop mic
- **Microphone (Realtek HD Audio)** - Desktop/external mic
- **Headset (Bluetooth)** - Boult Audio/CORE-WH3
- **Steam Streaming Microphone** - Virtual device

**Recommended:** Use **"Microphone Array (AMD Audio Device)"** or **"Realtek HD Audio"** as they are physical devices.

---

## 🔄 After Fixing

Once you've:
1. ✅ Selected the correct microphone
2. ✅ Unmuted and increased volume
3. ✅ Granted permissions
4. ✅ Tested in Windows Voice Recorder

**Restart the backend:**
```powershell
# Stop the backend (Ctrl+C in the terminal running it)
# Then restart:
cd "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"
python backend/api_service.py
```

**Test voice in the app:**
1. Open the desktop client
2. Click **🎙 Start Listening**
3. You should see a message: "Voice listening started"
4. Speak clearly into the microphone
5. Your speech should appear as text in the chat

---

## 🧪 Advanced: Test Voice Module

Run this diagnostic to verify everything works:

```powershell
cd "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"
python tests/manual/test_voice.py
```

Look for:
- ✅ Audio RMS level > 200 (means sound is detected)
- ✅ Transcription successful

---

## Still Not Working?

If you've tried everything above:

1. **Check which device is actually recording:**
   ```python
   import sounddevice as sd
   print(sd.query_devices())
   ```
   Look for the device with **max_input_channels > 0** and **default_samplerate**

2. **Manually select a different microphone:**
   Edit `backend/voice_engine/input/recorder.py` and add device ID:
   ```python
   sd.rec(..., device=1, ...)  # Try different numbers
   ```

3. **Use a USB headset or external microphone:**
   Built-in laptop mics sometimes have hardware issues

4. **Check for driver updates:**
   - Open Device Manager → **Sound, video and game controllers**
   - Right-click your audio device → **Update driver**

---

**Need Help?** Share the output of `python tests/manual/test_voice.py` for further debugging.

---

## TTS Voice And Accent Options (Piper)

Text-to-speech now supports configurable voice + accent profiles.

### Where To Configure

Edit the `tts` section in `backend/config/assistant_config.json`:

```json
"tts": {
   "active_voice": "danny",
   "active_accent": "en_US",
   "allow_accent_fallback": true,
   "voice_catalog": {
      "en_US": {
         "danny": "en_US-danny-low.onnx",
         "amy": "en_US-amy-medium.onnx"
      },
      "en_GB": {
         "jenny": "en_GB-jenny-high.onnx"
      }
   }
}
```

### Add New Voices / Accents

1. Copy Piper `.onnx` and `.onnx.json` files into `backend/voice_engine/tts/piper`.
2. Add the model filename to `tts.voice_catalog`.
3. Set `tts.active_voice` and `tts.active_accent`.
4. Restart backend.

If a selected voice is not installed, the assistant safely falls back to `en_US-danny-low.onnx`.

### Runtime API Support

- `GET /api/settings` now returns:
   - `tts_voice`
   - `tts_accent`
   - `tts_available_voices`
- `POST /api/settings` accepts:
   - `tts_voice`
   - `tts_accent`
- `POST /api/speak` accepts optional:
   - `voice`
   - `accent`
