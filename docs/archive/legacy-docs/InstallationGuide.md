# AI-Based Voice Enabled Intelligent System - Complete Installation Guide

🎙️ **Complete guide to set up an offline AI voice assistant for Windows desktop automation**

Includes Speech-to-Text (Whisper), Text-to-Speech (Piper), voice input/output, and automation tools.

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Project Setup](#project-setup)
4. [Voice Engine Configuration](#voice-engine-configuration)
5. [STT Setup (Whisper)](#stt-setup-whisper)
6. [TTS Setup (Piper)](#tts-setup-piper)
7. [Audio Device Configuration](#audio-device-configuration)
8. [Running the Application](#running-the-application)
9. [Verification Steps](#verification-steps)
10. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware Requirements
- **OS**: Windows 10 or later (Windows 11 recommended)
- **CPU**: Intel i5/Ryzen 5 or better (quad-core minimum)
- **RAM**: 8GB minimum (16GB+ recommended)
  - Whisper model: ~3-4GB
  - Piper TTS: ~500MB
  - System overhead: ~2GB
  - Running processes: ~1GB
- **Disk Space**: 25GB total
  - Whisper models: ~1.5GB
  - Piper TTS: ~500MB
  - Python/Dependencies: ~2GB
  - Free space for caching: ~20GB
- **Audio Hardware** (Required for voice):
  - Microphone (built-in or external)
  - Speaker or headphones
  - Audio drivers installed and working
- **GPU** (Optional but recommended):
  - NVIDIA GPU with CUDA compute capability 3.0+
  - 2GB+ VRAM for faster Whisper processing
  - CUDA Toolkit 11.8+ (if using GPU)

### Required Software
- **Python 3.10 or 3.11**
- **Git** (for version control)
- **Visual Studio Code** (optional but recommended)
- **ffmpeg** (optional, for audio processing)

### Supported NVIDIA GPUs
If you have an NVIDIA GPU, Whisper will auto-detect and use it for faster inference:
- GTX 1060 and higher
- RTX series (20xx, 30xx, 40xx)
- A10, A100 (data center GPUs)

---

## Prerequisites Installation

### Step 1: Install Python 3.10

1. Download from: https://www.python.org/downloads/
2. Run the installer
3. **IMPORTANT**: Check ✅ "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```powershell
   python --version
   ```
   Should show: `Python 3.10.x`

### Step 2: Install Git

1. Download from: https://git-scm.com/download/win
2. Run installer with default settings
3. Restart your terminal/PowerShell after installation
4. Verify installation:
   ```powershell
   git --version
   ```
   Should show: `git version x.x.x`

### Step 3: Install Visual Studio Code (Optional)

1. Download from: https://code.visualstudio.com/
2. Run installer and complete setup
3. Install Python extension:
   - Open VS Code
   - Press `Ctrl+Shift+X`
   - Search "Python"
   - Install Microsoft Python extension

### Step 4: Update Environment Variables (If commands not recognized)

If `python` or `git` commands don't work:

1. Press **Windows Key + X** → Select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Click **New** under "User variables"
5. Add these paths if they don't exist:
   ```
   C:\Program Files\Git\cmd
   C:\Program Files\Git\bin
   C:\Users\YourUsername\AppData\Local\Programs\Python\Python310
   C:\Users\YourUsername\AppData\Local\Programs\Python\Python310\Scripts
   ```
6. Click OK and restart PowerShell

---

## Project Setup

### Step 1: Clone the Repository

Open PowerShell or Git Bash and run:

```bash
cd D:\
mkdir "AI Based Voice Intelligent System"
cd "AI Based Voice Intelligent System"
git clone https://github.com/VanshRaghav5/AI-Based-Voice-Enabled-Intelligent-System-Assistant.git
cd AI-Based-Voice-Enabled-Intelligent-System-Assistant
```

### Step 2: Create Virtual Environment

The virtual environment isolates project dependencies from system Python.

```powershell
python -m venv venv
```

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

You should see `(venv)` at the start of your terminal line.

### Step 4: Install Dependencies

With virtual environment activated, run:

```powershell
pip install --upgrade pip
pip install -r backend/requirements.txt
```

This installs all required packages:
- FastAPI & Uvicorn (API framework)
- Whisper & PyTorch (Speech-to-Text)
- Sounddevice & SciPy (Audio processing)
- Automation tools (keyboard, pyautogui, send2trash)
- And more...

**Installation time**: ~5-15 minutes depending on internet speed

### Step 5: Install Additional Audio Dependencies (Optional)

For better audio support, install ffmpeg:

**Option A - Using Chocolatey:**
```powershell
choco install ffmpeg
```

**Option B - Manual download:**
1. Download from: https://ffmpeg.org/download.html
2. Extract to: `C:\ffmpeg`
3. Add to PATH (see Step 4 in Prerequisites)

---

## STT Setup (Whisper)

### What is Whisper?
OpenAI's Whisper is a robust speech recognition model that:
- **Recognizes 99+ languages** (English optimized)
- **Works offline** (no internet needed after download)
- **Multilingual capability** (automatic language detection)
- **GPU accelerated** (CUDA support)
- **Free and open-source**

### Model Options

| Model | Size | Memory | Speed | Accuracy | Best For |
|-------|------|--------|-------|----------|----------|
| tiny | 139MB | 1GB | 🚀 Fastest | Low | Testing, Low-power devices |
| base | 461MB | 2GB | 🚀 Fast | Medium | **Default choice** |
| small | 769MB | 3GB | ⚡ Medium | High | Most users (recommended) |
| medium | 1.4GB | 5GB | 🐢 Slow | Very high | Accuracy critical |
| large | 2.9GB | 10GB | 🐢 Very slow | Best | Professional use |

**Current project setting**: `small` model (~1.5 minutes download)

### Step 1: Download Whisper Model

The model is automatically downloaded on first run, but you can pre-download:

```powershell
# Navigate to project
cd "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"

# Activate venv
.\venv\Scripts\Activate.ps1

# Pre-download model (choose one)
python -c "import whisper; whisper.load_model('small')"   # Recommended
# or
python -c "import whisper; whisper.load_model('base')"    # Faster
```

**Download locations and sizes:**
```
C:\Users\YourUsername\.cache\whisper\
├── tiny.pt (139MB)
├── base.pt (461MB)
├── small.pt (769MB)        ← Current project default
├── medium.pt (1.4GB)
└── large.pt (2.9GB)
```

### Step 2: Configure Whisper Model

Edit `backend/config/settings.py`:

```python
# ==============================
# Whisper Settings
# ==============================

WHISPER_MODEL = "small"    # Change to: tiny, base, small, medium, large

# For very slow systems, use "base"
# For maximum accuracy, use "medium" or "large"
```

### Step 3: GPU Acceleration (Optional)

**Check if CUDA is available:**
```powershell
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
```

If `True` → CUDA is ready, Whisper will use it automatically  
If `False` → Will use CPU (slower but still works)

**For GPU users - Install NVIDIA CUDA Toolkit:**
1. Download from: https://developer.nvidia.com/cuda-downloads
2. Install to: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1`
3. Restart terminal
4. Verify: `nvidia-smi` (should show GPU info)

### Step 4: Test Whisper

```powershell
python -c "
import whisper
import torch

print(f'Device: {\"CUDA\" if torch.cuda.is_available() else \"CPU\"}')
model = whisper.load_model('small')
print('Whisper loaded successfully!')
"
```

---

## TTS Setup (Piper)

### What is Piper?
Piper is an open-source, offline text-to-speech engine that:
- **Runs completely offline** (no cloud needed)
- **Multiple voices available** (50+ languages)
- **Fast synthesis** (real-time audio generation)
- **Customizable** (speed, pitch, emotion)
- **Lightweight** (~500MB)

### Piper Configuration

The project includes **Piper binary and voice model**:

```
backend/voice_engine/tts/piper/
├── piper.exe                     # Main TTS executable
├── en_US-danny-low.onnx         # Voice model (Danny voice)
├── en_US-danny-low.onnx.json    # Model configuration
├── espeak-ng-data/              # Phoneme generation data
└── ...other voices
```

### Available Voice Options

The project comes with `danny-low` (male voice), but you can add more:

| Voice ID | Gender | Quality | Size |
|----------|--------|---------|------|
| en_US-danny-low | Male | Low (faster) | 24MB |
| en_US-danny | Male | Medium | 32MB |
| en_US-ljspeech | Female | High | 48MB |
| en_GB-northern_english-* | Various | Various | 20-60MB |
| en_US-hfc-medium | Female | Medium | 40MB |

### Step 1: Verify Piper Installation

Piper should already be installed. Verify:

```powershell
# Test if Piper is accessible
$piper_path = ".\backend\voice_engine\tts\piper\piper.exe"
if (Test-Path $piper_path) {
    Write-Host "✓ Piper executable found!"
} else {
    Write-Host "✗ Piper not found!"
}
```

### Step 2: Configure TTS Settings

Edit `backend/config/settings.py`:

```python
# ==============================
# TTS Settings
# ==============================

TTS_LENGTH_SCALE = "1.4"    # 1.0 = normal speed
                            # > 1.0 = slower
                            # < 1.0 = faster

TTS_NOISE_SCALE = "0.667"   # Voice variation (0.0-1.0)
                            # Lower = more consistent
                            # Higher = more natural/varied

TTS_NOISE_W = "0.8"         # Noise weight for prosody
                            # Affects speech expression
```

### Step 3: Test Piper

```powershell
# Simple test
python -c "
from backend.voice_engine.tts.tts_engine import speak_text
speak_text('Hello world! This is Piper text to speech.')
print('✓ Piper TTS working!')
"
```

**Expected output**: Your computer should speak the text in a male voice.

### Step 4: Add Additional Voices (Optional)

To add more voices:

1. Download voice file from: https://huggingface.co/rhasspy/piper-voices
2. Extract `.onnx` and `.onnx.json` files to: `backend/voice_engine/tts/piper/`
3. Update `tts_engine.py` to use the new voice file

---

## Audio Device Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root if needed:

```
DEBUG=True
LOG_LEVEL=INFO
WHISPER_MODEL=base
```

### CUDA Setup (Optional - For GPU Acceleration)

If you have an NVIDIA GPU and want to use CUDA:

1. Download CUDA Toolkit from: https://developer.nvidia.com/cuda-downloads
2. Install cuDNN from: https://developer.nvidia.com/cudnn
3. Add to your `.env` or environment:
   ```
   CUDA_VISIBLE_DEVICES=0
   ```

---

## Running the Application

### Method 1: Run Main Application

**Activate virtual environment first:**

```powershell
# Navigate to project directory
cd "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"

# Activate venv
.\venv\Scripts\Activate.ps1

# Run application
python app.py
```

### Audio Device Setup

#### Check Available Devices

```powershell
python -c "
import sounddevice as sd
print('Available Audio Devices:')
print(sd.query_devices())
"
```

#### Troubleshoot Microphone

1. **Windows Settings**:
   - Press **Windows+I** → Sound settings
   - Check microphone is not muted
   - Test microphone level

2. **Select Specific Device**:
   Edit `backend/voice_engine/input/recorder.py`:
   ```python
   # Add device parameter
   audio = sd.rec(..., device=2)  # Replace 2 with your device ID
   ```

#### Audio Recording Settings

Edit `backend/config/settings.py`:

```python
# ==============================
# Voice Recording Settings
# ==============================

RECORD_DURATION = 4      # Seconds to record (increase for slower talkers)
SAMPLE_RATE = 16000      # CD quality (don't change for Whisper compatibility)
```

#### Hotkeys Configuration

Edit `backend/voice_engine/audio_pipeline.py`:

```python
PUSH_TO_TALK_KEY = "space"      # Change to: ctrl+alt+space, f3, etc.
TEXT_INPUT_HOTKEY = "ctrl+t"    # Change for text input mode
```

---

## Running the Application

### Step 1: Pre-Run Checklist

✅ Python 3.10+ installed  
✅ Git installed  
✅ Repository cloned  
✅ Virtual environment created  
✅ Dependencies installed  
✅ Whisper model downloaded  
✅ Microphone and speaker working  
✅ Audio devices detected  

### Step 2: Activate Virtual Environment

**Navigate to project:**
```powershell
cd "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"
```

**Activate venv (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Activate venv (Command Prompt):**
```powershell
.\venv\Scripts\activate.bat
```

You should see `(venv)` in your terminal.

### Method 1: Run Main Voice Assistant (RECOMMENDED)

This starts the full voice-controlled assistant with STT and TTS:

```powershell
# From project root with activated venv
python app.py
```

**Expected output:**
```
2026-02-28 17:56:11,057 - INFO - Assistant started. Say 'exit' to quit.
2026-02-28 17:56:11,083 - INFO - Assistant ready. Hold SPACE to talk or press CTRL+T to type.
```

**Usage:**
- **Hold SPACE**: Speak your command (4-second recording)
- **Press CTRL+T**: Type your command instead
- **Say "exit"**: Stop the assistant

### Method 2: Test Individual Components

**Test STT (Speech-to-Text):**
```powershell
python -c "
from backend.voice_engine.input.recorder import record_audio
from backend.voice_engine.stt.whisper_engine import transcribe_audio

print('Recording for 4 seconds... speak something!')
audio_path = record_audio()
text = transcribe_audio(audio_path)
print(f'You said: {text}')
"
```

**Test TTS (Text-to-Speech):**
```powershell
python -c "
from backend.voice_engine.tts.tts_engine import speak_text
speak_text('Hello! This is the text to speech engine.')
print('✓ TTS works!')
"
```

**Test Full Audio Pipeline:**
```powershell
python -c "
from backend.voice_engine.audio_pipeline import listen, speak

print('Testing voice pipeline...')
speak('Speak something, then I will repeat it.')
text = listen()  # Hold SPACE and speak
speak(f'You said: {text}')
"
```

### Method 3: Run Backend API Server

```powershell
cd backend
python -m uvicorn app:app --reload
```

Access at: `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

### Method 4: Run Tests

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

## Verification Steps

### Step 1: Verify Python Installation

```powershell
python --version
```
Should show: `Python 3.10.x` or higher

### Step 2: Verify Git Installation

```powershell
git --version
```
Should show: `git version x.x.x`

### Step 3: Verify Virtual Environment

```powershell
# Inside activated venv
pip list
```
Should show all installed packages including: `torch`, `openai-whisper`, `sounddevice`, `scipy`

### Step 4: Verify Whisper

```powershell
python -c "
import whisper
import torch
print(f'✓ Whisper installed')
print(f'✓ PyTorch installed')
print(f'✓ CUDA: {\"Yes\" if torch.cuda.is_available() else \"No\"}')
model = whisper.load_model('small')
print(f'✓ Model loaded successfully on {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')

print(f'✓ Model loaded successfully on {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
"
```

### Step 5: Verify Audio Devices

```powershell
python -c "
import sounddevice as sd
import scipy
import scipy.io.wavfile as wav

print('✓ sounddevice installed')
print('✓ scipy installed')

devices = sd.query_devices()
print(f'✓ Found {len(devices)} audio devices')

# List devices
for i, device in enumerate(devices):
    print(f'  [{i}] {device[\"name\"]}')"
"
```

### Step 6: Verify Piper TTS

```powershell
python -c "
import os
piper_path = './backend/voice_engine/tts/piper/piper.exe'
if os.path.exists(piper_path):
    print('✓ Piper executable found')
else:
    print('✗ Piper not found')
    
voice_model = './backend/voice_engine/tts/piper/en_US-danny-low.onnx'
if os.path.exists(voice_model):
    print('✓ Voice model found')
else:
    print('✗ Voice model not found')"
"
```

### Step 7: Full Verification Script

Run all checks at once:

```powershell
python -c "
import sys
import os
import subprocess

print('╔════════════════════════════════════════════════════════════╗')
print('║     AI Voice Assistant - Installation Verification         ║')
print('╚════════════════════════════════════════════════════════════╝')

# Python
print(f'\n✓ Python: {sys.version.split()[0]}')

# Torch
try:
    import torch
    device = 'CUDA' if torch.cuda.is_available() else 'CPU'
    print(f'✓ PyTorch: v{torch.__version__} ({device})')
except ImportError:
    print('✗ PyTorch not found')

# Whisper
try:
    import whisper
    print(f'✓ Whisper installed')
except ImportError:
    print('✗ Whisper not found')

# Audio
try:
    import sounddevice as sd
    print(f'✓ Audio devices: {len(sd.query_devices())} available')
except ImportError:
    print('✗ Sounddevice not found')

# Scipy
try:
    import scipy
    print(f'✓ SciPy: v{scipy.__version__}')
except ImportError:
    print('✗ SciPy not found')

# FastAPI
try:
    import fastapi
    print(f'✓ FastAPI: v{fastapi.__version__}')
except ImportError:
    print('✗ FastAPI not found')

# Piper
piper_path = './backend/voice_engine/tts/piper/piper.exe'
if os.path.exists(piper_path):
    print(f'✓ Piper TTS: Found')
else:
    print(f'✗ Piper TTS: Not found at {piper_path}')

print('\n╔════════════════════════════════════════════════════════════╗')
print('║              Ready to run: python app.py                   ║')
print('╚════════════════════════════════════════════════════════════╝')
"
"
```

---

✅ Python 3.10+ installed  
✅ Git installed  
✅ Repository cloned  
✅ Virtual environment created: `python -m venv venv`  
✅ Virtual environment activated: `.\venv\Scripts\Activate.ps1`  
✅ Dependencies installed: `pip install -r backend/requirements.txt`  
✅ Whisper model downloaded (auto-downloads on first run)  
✅ Application runs: `python app.py`  

---

## Troubleshooting

### Error: "python" is not recognized

**Solution:**
```powershell
# Add Python to PATH
$env:Path += ";C:\Users\YourUsername\AppData\Local\Programs\Python\Python310"
```

Or re-run Python installer and check "Add Python to PATH"

---

### Error: Cannot load venv activation script

**Solution:**
```powershell
# Set execution policy (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
.\venv\Scripts\Activate.ps1
```

Or use Command Prompt instead:
```cmd
.\venv\Scripts\activate.bat
```

---

### Error: "ModuleNotFoundError: No module named 'send2trash'"

**Solution:**
```powershell
# Reinstall dependencies
pip install -r backend/requirements.txt --force-reinstall
```

---

### Error: Whisper SHA256 Checksum Error

**Solution:**
```powershell
# Delete corrupted model
rm C:\Users\YourUsername\.cache\whisper\small.pt

# Run app again to re-download
python app.py
```

---

### Error: "git is not recognized"

**Solution:**
1. Restart PowerShell after installing Git
2. Or use Git Bash instead
3. Add to PATH: `C:\Program Files\Git\cmd`

---

### Application Runs Slowly

**Possible causes:**
- First run: Whisper model is loading (~30-60 seconds)
- CPU-only mode: Consider GPU acceleration with CUDA
- Available RAM: Close other applications

---

### Port Already in Use Error

**Solution:**
```powershell
# Kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change port in app.py
```

---

## File Structure

```
AI-Based-Voice-Enabled-Intelligent-System-Assistant/
├── app.py                          # Main application entry point
├── backend/
│   ├── app.py                      # Backend API server
│   ├── requirements.txt            # Python dependencies
│   ├── automation/                 # Automation tools
│   ├── core/                       # Core functionality
│   ├── llm/                        # LLM integration
│   ├── voice_engine/               # Speech processing
│   ├── memory/                     # Session memory
│   └── config/                     # Configuration
├── tests/                          # Unit tests
├── venv/                           # Virtual environment (created locally)
├── InstallationGuide.md            # This file
└── requirements-test.txt           # Testing dependencies
```

---

## Next Steps

1. **Explore the project**: Check `README.md` for feature documentation
2. **Run tests**: `pytest` to verify installation
3. **Review examples**: Check `example_*.py` files
4. **Configure settings**: Edit `backend/config/settings.py` as needed

---

## Getting Help

- **GitHub Issues**: https://github.com/VanshRaghav5/AI-Based-Voice-Enabled-Intelligent-System-Assistant/issues
- **Check logs**: Look in console output for error messages
- **Review test files**: `tests/` folder has working code examples

---

## System Specifications Used in Development

- **Windows 10/11**
- **Python 3.10**
- **Ram: 8GB+**
- **NVIDIA GPU with CUDA (optional)**

---

## Additional Resources

- **Whisper Documentation**: https://github.com/openai/whisper
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Python Virtual Environments**: https://docs.python.org/3/tutorial/venv.html
- **Git Basics**: https://git-scm.com/book/en/v2

---

**Last Updated**: February 28, 2026  
**Version**: 2.2.0  
**Status**: Ready for Production
