# 🎙️ AI-Based Voice Enabled Intelligent System - Complete Installation Guide

**Comprehensive step-by-step guide to set up an offline AI voice assistant for Windows with Speech-to-Text (Whisper), Text-to-Speech (Piper), and desktop automation.**

Last Updated: February 28, 2026 | Version: 2.2.0

---

## 📋 Table of Contents
1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Project Setup](#project-setup)
4. [Voice Engine Configuration](#voice-engine-configuration)
   - [STT Setup (Whisper)](#stt-setup-whisper)
   - [TTS Setup (Piper)](#tts-setup-piper)
   - [Audio Devices](#audio-devices)
5. [Running the Application](#running-the-application)
6. [Verification Steps](#verification-steps)
7. [Troubleshooting](#troubleshooting)
8. [Additional Resources](#additional-resources)

---

## 🖥️ System Requirements

### Hardware Requirements
- **OS**: Windows 10 or later (Windows 11 recommended)
- **CPU**: Intel i5/Ryzen 5 or better (quad-core minimum)
- **RAM**: 8GB minimum (16GB+ recommended)
  - Whisper model processing: ~3-4GB
  - Piper TTS engine: ~500MB
  - Python runtime: ~1-2GB
  - System baseline: ~1-2GB
  - Free applications: ~1GB
- **Disk Space**: 25GB total (5GB free minimum)
  - Whisper models: 1.5GB
  - Piper TTS with voices: 500MB
  - Python + dependencies: 2GB
  - Git repository: 500MB
  - Cache and temporary: 20GB
- **Audio Hardware** (REQUIRED for voice):
  - ✅ Microphone (built-in or USB)
  - ✅ Speaker/Headphones
  - ✅ Audio drivers installed
- **Network**: Internet for initial setup (can work offline after)

### GPU (Optional but Recommended)
- **NVIDIA GPU**: GTX 1060 or better, RTX series 20xx/30xx/40xx
- **VRAM**: 2GB+ (4GB+ recommended)
- **CUDA Compute Capability**: 3.0 or higher
- **Benefit**: 5-10x faster Whisper transcription

### Required Software
- **Python**: 3.10 or 3.11
- **Git**: Latest version
- **VS Code**: Optional but recommended
- **ffmpeg**: Optional (for advanced audio)

---

## 🔧 Prerequisites Installation

### Step 1: Install Python 3.10

1. **Download**: https://www.python.org/downloads/release/python-3100/
2. **Run installer**:
   - ✅ Check "Add Python to PATH" 
   - Select "Install Now"
3. **Verify installation**:
   ```powershell
   python --version
   ```
   Expected: `Python 3.10.x`

### Step 2: Install Git for Windows

1. **Download**: https://git-scm.com/download/win
2. **Run installer** with default settings
3. **Restart terminal** (important!)
4. **Verify**:
   ```powershell
   git --version
   ```
   Expected: `git version x.x.x`

### Step 3: Install Visual Studio Code (Optional)

1. **Download**: https://code.visualstudio.com/
2. **Install and open**
3. **Install Python extension**:
   - Press `Ctrl+Shift+X`
   - Search "Python"
   - Install Microsoft Python extension

### Step 4: Update PATH Environment Variables

If Step 1-2 doesn't work:

1. Press **Windows Key + X** → Select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Add these paths (if missing):
   ```
   C:\Program Files\Git\cmd
   C:\Program Files\Git\bin
   C:\Users\YourUsername\AppData\Local\Programs\Python\Python310
   C:\Users\YourUsername\AppData\Local\Programs\Python\Python310\Scripts
   ```
5. Click **OK**, restart PowerShell

### Step 5: Install ffmpeg (Optional for audio processing)

```powershell
# Option A: Via Chocolatey
choco install ffmpeg

# Option B: Via direct download
# Download: https://ffmpeg.org/download.html
# Extract to: C:\ffmpeg
# Add to PATH (Step 4)
```

---

## 📦 Project Setup

### Step 1: Clone Repository

```bash
cd D:\
mkdir "AI Based Voice Intelligent System"
cd "AI Based Voice Intelligent System"
git clone https://github.com/VanshRaghav5/AI-Based-Voice-Enabled-Intelligent-System-Assistant.git
cd AI-Based-Voice-Enabled-Intelligent-System-Assistant
```

### Step 2: Create Virtual Environment

```powershell
python -m venv venv
```

Creates isolated Python environment for this project.

### Step 3: Activate Virtual Environment

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt (CMD):**
```cmd
.\venv\Scripts\activate.bat
```

**Git Bash:**
```bash
source venv/Scripts/activate
```

✅ You should see `(venv)` at the start of each terminal line.

### Step 4: Install Dependencies

```powershell
pip install --upgrade pip
pip install -r backend/requirements.txt
```

**Installs:**
- fastapi, uvicorn (API framework)
- torch, openai-whisper (Speech recognition)
- pydantic (data validation)
- keyboard, pyautogui (automation)
- sounddevice, scipy (audio)
- And 10+ more packages

⏱️ Installation time: 10-20 minutes (varies by internet)

---

## 🎙️ Voice Engine Configuration

### Overview

```
Audio Input (Microphone)
        ↓
[Sounddevice] Record Audio → .wav file
        ↓
[Whisper - STT] Transcribe → Text
        ↓
[Processing]
        ↓
[Piper - TTS] Generate Speech → Audio
        ↓
Speaker Output
```

---

## 🗣️ STT Setup (Whisper)

### What is Whisper?
OpenAI's speech recognition model:
- ✅ Recognizes 99+ languages
- ✅ Works completely offline
- ✅ GPU accelerated (optional)
- ✅ Free and open-source
- ✅ Accuracy: 95%+ on clear audio

### Available Models

| Model | Size | Memory | Speed | Accuracy | Best For |
|-------|------|--------|-------|----------|----------|
| **tiny** | 139MB | 1GB | 🚀🚀 Very fast | ⭐⭐ Low | Testing, weak devices |
| **base** | 461MB | 2GB | 🚀 Fast | ⭐⭐⭐ Medium | Good balance |
| **small** | 769MB | 3GB | ⚡ Medium | ⭐⭐⭐⭐ High | **Recommended** |
| **medium** | 1.4GB | 5GB | 🐢 Slow | ⭐⭐⭐⭐⭐ Very high | Accuracy critical |
| **large** | 2.9GB | 10GB | 🐢🐢 Very slow | ⭐⭐⭐⭐⭐ Best | Professional use |

**Project Default**: `small` (good balance of size, speed, accuracy)

### Step 1: Pre-Download Whisper Model

Models auto-download on first run, but pre-download for offline use:

```powershell
# Navigate to project
cd "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"

# Activate venv
.\venv\Scripts\Activate.ps1

# Download "small" model (recommended)
python -c "import whisper; whisper.load_model('small')"
```

**Download sizes:**
- `small`: ~1.5GB (downloads as 769MB)
- `base`: ~500MB
- `tiny`: ~200MB

**Cache location:**
```
C:\Users\YourUsername\.cache\whisper\
├── tiny.pt
├── base.pt
├── small.pt        ← Current setting
├── medium.pt
└── large.pt
```

### Step 2: Configure Whisper Model

Edit **`backend/config/settings.py`**:

```python
# ==============================
# Whisper Settings
# ==============================

WHISPER_MODEL = "small"    # Options: tiny, base, small, medium, large
```

**Choose based on your system:**
- 🐢 Weak system (4GB RAM): use `"base"`
- ⚡ Good system (8GB RAM): use `"small"` (recommended)
- 🎯 Accuracy critical: use `"medium"`

### Step 3: Enable GPU Acceleration (Optional but Recommended)

**Check if CUDA available:**
```powershell
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

If `True` → GPU ready ✅  
If `False` → Uses CPU (works but slower)

**Install NVIDIA CUDA Toolkit** (if you have NVIDIA GPU):
1. Download: https://developer.nvidia.com/cuda-downloads
2. Install to: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1`
3. Restart terminal
4. Verify: `nvidia-smi` (shows GPU info)

### Step 4: Test Whisper

```powershell
python -c "
import whisper
import torch

device = 'CUDA' if torch.cuda.is_available() else 'CPU'
print(f'Device: {device}')
model = whisper.load_model('small')
print('✓ Whisper loaded successfully!')
"
```

---

## 🔊 TTS Setup (Piper)

### What is Piper?
Offline text-to-speech engine:
- ✅ 100% offline (no cloud needed)
- ✅ Natural sounding voices
- ✅ Customizable speed/pitch
- ✅ Real-time synthesis
- ✅ Lightweight (~500MB)

### Built-in Voice

**Current voice**: `en_US-danny-low` (male voice, fast, medium quality)

```
backend/voice_engine/tts/piper/
├── piper.exe                      # TTS executable
├── en_US-danny-low.onnx          # Voice model (24MB)
├── en_US-danny-low.onnx.json     # Configuration
└── espeak-ng-data/               # Phoneme data
```

### Available Alternative Voices

Download from: https://huggingface.co/rhasspy/piper-voices

| Voice | Gender | Quality | Size |
|-------|--------|---------|------|
| danny-low | Male | Low | 24MB |
| danny | Male | Medium | 32MB |
| ljspeech | Female | High | 48MB |
| mls_us_arctic-bdl | Multiple | Various | 30-50MB |

### Step 1: Verify Piper Installation

```powershell
$piper_path = ".\backend\voice_engine\tts\piper\piper.exe"
$voice_path = ".\backend\voice_engine\tts\piper\en_US-danny-low.onnx"

if ((Test-Path $piper_path) -and (Test-Path $voice_path)) {
    Write-Host "✓ Piper TTS: Ready!"
} else {
    Write-Host "✗ Piper: Missing files"
}
```

### Step 2: Configure TTS Settings

Edit **`backend/config/settings.py`**:

```python
# ==============================
# TTS Settings
# ==============================

TTS_LENGTH_SCALE = "1.4"    # Speed (1.0=normal, >1.0=slower, <1.0=faster)
TTS_NOISE_SCALE = "0.667"   # Variation (0.0=consistent, 1.0=varied)
TTS_NOISE_W = "0.8"         # Emotion/prosody (affects expression)
```

**Preset configurations:**

Fast & Natural:
```python
TTS_LENGTH_SCALE = "1.0"
TTS_NOISE_SCALE = "0.8"
TTS_NOISE_W = "1.0"
```

Clear & Slow:
```python
TTS_LENGTH_SCALE = "1.6"
TTS_NOISE_SCALE = "0.5"
TTS_NOISE_W = "0.6"
```

### Step 3: Test Piper

```powershell
python -c "
from backend.voice_engine.tts.tts_engine import speak_text
speak_text('Hello! This is Piper text to speech. Testing voice output.')
print('✓ Piper TTS working!')
"
```

**Expected**: Computer speaks the text in male voice

### Step 4: Add Custom Voice (Optional)

1. Download `.onnx` and `.onnx.json` from HuggingFace
2. Place in: `backend/voice_engine/tts/piper/`
3. Edit `backend/voice_engine/tts/tts_engine.py`:
   ```python
   VOICE_MODEL = os.path.join(PIPER_DIR, "en_US-ljspeech.onnx")
   VOICE_CONFIG = os.path.join(PIPER_DIR, "en_US-ljspeech.onnx.json")
   ```

---

## 🎤 Audio Devices

### Step 1: Check Audio Devices

```powershell
python -c "
import sounddevice as sd
print('Audio Devices:')
for i, device in enumerate(sd.query_devices()):
    print(f'[{i}] {device}')
"
```

### Step 2: Configure Recording

Edit **`backend/config/settings.py`**:

```python
# ==============================
# Voice Recording Settings
# ==============================

RECORD_DURATION = 4      # Seconds (increase for slower speakers)
SAMPLE_RATE = 16000      # Hz (DON'T CHANGE - Whisper requirement)
```

### Step 3: Select Specific Microphone (If needed)

Edit `backend/voice_engine/input/recorder.py`:

```python
# Find your mic ID, then add to rec() call
audio = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype='int16',
    device=2  # Replace 2 with your mic ID from Step 1
)
```

### Step 4: Configure Hotkeys

Edit `backend/voice_engine/audio_pipeline.py`:

```python
PUSH_TO_TALK_KEY = "space"      # Hold to record: space, f3, ctrl+alt+s
TEXT_INPUT_HOTKEY = "ctrl+t"    # Type instead: ctrl+t, alt+q
```

Common alternatives:
- `"f3"` - Function key
- `"ctrl+alt+space"` - Ctrl+Alt combo
- `"capslock"` - Caps lock key

### Step 5: Troubleshoot Audio

**Check microphone permissions:**
1. Settings → Privacy & Security → Microphone
2. Ensure Python has access

**Test recording:**
```powershell
python -c "
from backend.voice_engine.input.recorder import record_audio
print('Recording 4 seconds... speak!')
path = record_audio()
print(f'Saved to: {path}')
"
```

**Check speaker volume:**
1. Click taskbar volume icon
2. Set to 50-100%
3. Test with: `python -c \"from backend.voice_engine.tts.tts_engine import speak_text; speak_text('Sound test')\"`

---

## ▶️ Running the Application

### Pre-Run Checklist

- ✅ Python 3.10+ installed
- ✅ Git installed
- ✅ Repository cloned
- ✅ venv created and activated
- ✅ Dependencies installed
- ✅ Whisper model downloaded
- ✅ Microphone working
- ✅ Speaker working

### Activate Virtual Environment

```powershell
cd "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"
.\venv\Scripts\Activate.ps1
```

You should see: `(venv)` at terminal start

### Method 1: Full Voice Assistant (RECOMMENDED)

```powershell
python app.py
```

**Output:**
```
2026-02-28 17:56:11 - INFO - Assistant started. Say 'exit' to quit.
2026-02-28 17:56:11 - INFO - Assistant ready. Hold SPACE to talk or press CTRL+T to type.
```

**Usage:**
- 🎤 **Hold SPACE**: Speak command (records 4 seconds)
- ⌨️ **Press CTRL+T**: Type command instead
- 🚪 **Say "exit"**: Stop assistant

### Method 2: Test Speech-to-Text Only

```powershell
python -c "
from backend.voice_engine.input.recorder import record_audio
from backend.voice_engine.stt.whisper_engine import transcribe_audio

print('Hold SPACE to record... (4 seconds)')
audio_path = record_audio()
print('Transcribing...')
text = transcribe_audio(audio_path)
print(f'You said: \"{text}\"')
"
```

### Method 3: Test Text-to-Speech Only

```powershell
python -c "
from backend.voice_engine.tts.tts_engine import speak_text
speak_text('Hello world! This is Piper TTS speaking.')
print('✓ TTS test complete!')
"
```

### Method 4: Test Full Audio Pipeline

```powershell
python -c "
from backend.voice_engine.audio_pipeline import listen, speak

print('Testing full pipeline...')
speak('Please say something after the beep.')
text = listen()  # Hold SPACE and speak
speak(f'You said: {text}')
"
```

### Method 5: Run Backend API Server

```powershell
cd backend
python -m uvicorn app:app --reload
```

Access: http://localhost:8000  
Docs: http://localhost:8000/docs

### Method 6: Run Tests

```powershell
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run specific test
pytest tests/test_stt_module.py -v

# Run with coverage
pytest --cov=backend tests/
```

---

## ✅ Verification Steps

### Test 1: Python & Packages

```powershell
python -c "
import sys
print(f'Python: {sys.version}')

packages = ['torch', 'whisper', 'fastapi', 'sounddevice', 'scipy']
for pkg in packages:
    try:
        mod = __import__(pkg)
        print(f'✓ {pkg}')
    except:
        print(f'✗ {pkg}')
"
```

### Test 2: GPU Support

```powershell
python -c "
import torch
if torch.cuda.is_available():
    print(f'✓ CUDA Ready: {torch.cuda.get_device_name(0)}')
else:
    print('✓ CPU Mode (will work but slower)')
"
```

### Test 3: Whisper

```powershell
python -c "
import whisper
import torch
device = 'CUDA' if torch.cuda.is_available() else 'CPU'
print(f'Loading Whisper ({device})...')
model = whisper.load_model('small')
print('✓ Whisper ready')
"
```

### Test 4: Audio Devices

```powershell
python -c "
import sounddevice as sd
devices = sd.query_devices()
print(f'✓ Found {len(devices)} audio devices')
for i, d in enumerate(devices):
    print(f'  [{i}] {d[\"name\"]}'
```

### Test 5: Piper TTS

```powershell
python -c "
import os
piper = './backend/voice_engine/tts/piper/piper.exe'
voice = './backend/voice_engine/tts/piper/en_US-danny-low.onnx'
print(f'Piper: {\"✓\" if os.path.exists(piper) else \"✗\"}')
print(f'Voice: {\"✓\" if os.path.exists(voice) else \"✗\"}')
"
```

### Full Verification Script

```powershell
python -c "
import sys, os, torch, whisper, sounddevice as sd

print('╔════════════════════════════════════════════════════════════╗')
print('║     AI Voice Assistant - System Verification               ║')
print('╚════════════════════════════════════════════════════════════╝')

print(f'\n✓ Python: {sys.version.split()[0]}')
print(f'✓ PyTorch: v{torch.__version__}')
print(f'✓ Whisper: Installed')
print(f'✓ Audio: {len(sd.query_devices())} devices')
device = 'CUDA' if torch.cuda.is_available() else 'CPU'
print(f'✓ Mode: {device}')

piper = './backend/voice_engine/tts/piper/piper.exe'
print(f'✓ Piper: {\"Ready\" if os.path.exists(piper) else \"Missing\"}')

print('\n╔════════════════════════════════════════════════════════════╗')
print('║  All systems ready! Run: python app.py                     ║')
print('╚════════════════════════════════════════════════════════════╝')
"
```

---

## ❌ Troubleshooting

### Microphone Issues

#### Problem: No audio input / Mic not detected

```powershell
# Step 1: List devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Step 2: Check Windows permissions
# Settings → Privacy & Security → Microphone → Allow Python

# Step 3: Test specific device
# Edit recorder.py, add: device=2  (replace 2 with your device ID)

# Step 4: Use Windows test
# Settings → Sound settings → Test microphone
```

#### Problem: Recording too quiet

```python
# In backend/config/settings.py, increase duration:
RECORD_DURATION = 6  # Instead of 4

# Then test:
python -c "
from backend.voice_engine.input.recorder import record_audio
import os
path = record_audio()
size = os.path.getsize(path)
print(f'File size: {size} bytes')
"
```

#### Problem: Speaker/TTS audio not playing

```powershell
# Step 1: Check volume
# Click taskbar volume, set to 50%+

# Step 2: Check device
python -c "import sounddevice as sd; print(sd.query_devices())"

# Step 3: Edit tts_engine.py, add device ID:
# sd.play(audio, samplerate=rate, device=1)

# Step 4: Test
python -c "from backend.voice_engine.tts.tts_engine import speak_text; speak_text('Test')"
```

---

### Whisper Issues

#### Problem: Import error / Whisper not found

```powershell
pip install openai-whisper --upgrade
```

#### Problem: CUDA out of memory

```powershell
# Option 1: Force CPU
# In backend/voice_engine/stt/whisper_engine.py:
DEVICE = "cpu"

# Option 2: Use smaller model
# In backend/config/settings.py:
WHISPER_MODEL = "tiny"

# Option 3: Update PyTorch for your GPU
pip uninstall torch -y
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

#### Problem: SHA256 Checksum Error

```powershell
# Delete corrupted model
rm C:\Users\YourUsername\.cache\whisper\small.pt

# Re-run app to re-download
python app.py
```

#### Problem: Very slow transcription

```powershell
# Check GPU usage
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# If False, install CUDA:
# https://developer.nvidia.com/cuda-downloads

# Or use smaller model:
# WHISPER_MODEL = "base"  # In settings.py
```

---

### Piper TTS Issues

#### Problem: Piper executable not found

```powershell
# Verify file exists
Test-Path ".\backend\voice_engine\tts\piper\piper.exe"

# If missing, re-clone repo or download:
# https://github.com/rhasspy/piper
```

#### Problem: Garbled audio / Poor quality

```python
# In backend/config/settings.py, adjust:
TTS_LENGTH_SCALE = "1.2"    # Slower = clearer
TTS_NOISE_SCALE = "0.5"     # Lower = consistent
TTS_NOISE_W = "0.6"         # Different expressiveness
```

---

### General Setup

#### Problem: "python" not recognized

```powershell
# Add to PATH (Step 4 in Prerequisites)
$env:Path += ";C:\Users\YourUsername\AppData\Local\Programs\Python\Python310"

# Or run permanently:
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Users\YourUsername\AppData\Local\Programs\Python\Python310", "User")
```

#### Problem: Virtual environment won't activate

```powershell
# Try direct path
C:\path\to\venv\Scripts\activate.ps1

# Or use command prompt instead
.\venv\Scripts\activate.bat

# Or set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Problem: "ModuleNotFoundError"

```powershell
# Reinstall dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt --force-reinstall

# Or install specific package
pip install -U openai-whisper
```

#### Problem: Port 8000 already in use

```powershell
# Find process
netstat -ano | findstr :8000

# Kill it (replace 12345 with PID)
taskkill /PID 12345 /F

# Or use different port
python -m uvicorn backend.app:app --port 8001
```

---

## 📂 Project Structure

```
AI-Based-Voice-Enabled-Intelligent-System-Assistant/
│
├── app.py                          # 🎯 Main entry point
│
├── backend/
│   ├── app.py                      # API server
│   ├── requirements.txt            # Dependencies
│   │
│   ├── voice_engine/               # 🎙️ Voice processing
│   │   ├── input/
│   │   │   └── recorder.py         # Microphone recording
│   │   ├── stt/
│   │   │   └── whisper_engine.py   # Speech-to-Text
│   │   ├── tts/
│   │   │   ├── tts_engine.py       # Text-to-Speech
│   │   │   └── piper/              # TTS binary & voices
│   │   └── audio_pipeline.py       # Main voice orchestration
│   │
│   ├── automation/                 # 🛠️ Automation tools
│   │   ├── file/                   # File operations
│   │   ├── system/                 # System control
│   │   └── app_launcher.py         # Application launching
│   │
│   ├── core/                       # ⚙️ Core engine
│   │   ├── assistant_controller.py # Main controller
│   │   ├── executor.py             # Command execution
│   │   └── tool_registry.py        # Tool management
│   │
│   ├── config/                     # ⚙️ Configuration
│   │   ├── settings.py             # STT/TTS/Recording settings
│   │   └── logger.py               # Logging
│   │
│   ├── llm/                        # 🧠 LLM integration
│   │   └── llm_client.py           # LLM interface
│   │
│   └── memory/                     # 💾 Session storage
│       └── session_state.py        # Session management
│
├── tests/                          # ✅ Unit tests
│   ├── test_stt_module.py
│   ├── test_tts_module.py
│   └── test_*.py
│
├── venv/                           # Python virtual environment (created locally)
│
├── InstallationGuide.md            # This file
├── COMPLETE_INSTALLATION_GUIDE.md  # Extended guide
├── README.md                       # Feature documentation
└── requirements-test.txt           # Test dependencies
```

---

## 🚀 Next Steps

1. **Complete Setup**: Follow guide Step 1-5
2. **Test Components**: Run verification tests
3. **Configure Settings**: Edit `backend/config/settings.py` for your system
4. **Run Assistant**: `python app.py`
5. **Add Customizations**: Add automation tools or custom voices
6. **Review Examples**: Check `example_*.py` files
7. **Run Tests**: `pytest tests/`

---

## 📚 Additional Resources

- **Whisper Docs**: https://github.com/openai/whisper
- **Piper Docs**: https://github.com/rhasspy/piper
- **FastAPI**: https://fastapi.tiangolo.com/
- **Python venv**: https://docs.python.org/3/tutorial/venv.html
- **Git**: https://git-scm.com/book/en/v2
- **CUDA**: https://developer.nvidia.com/cuda-downloads

---

## 💬 Getting Help

- **GitHub Issues**: https://github.com/VanshRaghav5/AI-Based-Voice-Enabled-Intelligent-System-Assistant/issues
- **Check Logs**: Console output has detailed error messages
- **Review Tests**: `tests/` folder has working examples
- **Check README.md**: Feature and architecture documentation

---

## 📊 System Recommendations

### Budget Build (Minimum)
- CPU: Intel i5-8th Gen
- RAM: 8GB
- GPU: None (will use CPU)
- Time: ~2 hours setup, slower transcription

### Recommended Build
- CPU: Intel i7 / Ryzen 7 (10th Gen+)
- RAM: 16GB
- GPU: NVIDIA GTX 1660 or RTX 3060
- Time: ~1 hour setup, fast transcription

### Professional Build
- CPU: Intel i9 / Ryzen 9
- RAM: 32GB+
- GPU: NVIDIA RTX 3080/4090
- Time: ~30 min setup, real-time transcription

---

## 📝 Document Info

- **Created**: February 28, 2026
- **Last Updated**: February 28, 2026
- **Project Version**: 2.2.0
- **Status**: Production Ready ✅
- **Python Supported**: 3.10, 3.11
- **OS**: Windows 10+ only

---

**Happy voice assisting! 🎉**
