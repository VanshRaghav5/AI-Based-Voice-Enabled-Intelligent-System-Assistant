# OmniAssist AI -- Voice-Enabled Intelligent System Assistant

OmniAssist AI is a hybrid (offline-first) voice-enabled intelligent
assistant designed to enhance human--computer interaction. It listens to
user speech, understands it using AI models, and responds naturally
using high-quality text-to-speech, with controlled system access.

This project is developed as an academic mini-project with a focus on
offline capability, modular architecture, and production-ready design.

------------------------------------------------------------------------

## 🚀 Key Features

-   🎙️ Real-time voice input through microphone
-   🧠 Offline speech-to-text using Whisper
-   🔊 Offline neural text-to-speech using Piper
-   🌐 FastAPI backend for modular API-based control
-   🧩 Clean separation of voice, API, and logic layers
-   🔐 Privacy-friendly (offline by default)

------------------------------------------------------------------------

## 🧠 Current System Architecture

User Speech\
↓\
Microphone Input\
↓\
Whisper (Speech-to-Text -- Offline)\
↓\
Intent / Logic Layer (Upcoming)\
↓\
Piper (Text-to-Speech -- Offline)\
↓\
Audio Response

------------------------------------------------------------------------

## 📁 Project Structure

OmniAssist-AI/

backend/\
    app.py\
    requirements.txt

    api/\
        voice.py

    voice/\
        recorder.py\
        stt.py\
        tts.py\
        piper/ (local runtime -- ignored in Git)

desktop-app/ (Future UI)\
docs/\
README.md

------------------------------------------------------------------------

## 🛠️ Technologies Used

-   Python 3.10+
-   FastAPI
-   Whisper (Offline STT)
-   Piper TTS (Offline TTS)
-   SoundDevice & SciPy
-   Uvicorn

------------------------------------------------------------------------

## ⚙️ Setup Instructions

1.  Clone the repository\
    git clone `<repository-url>`{=html}\
    cd OmniAssist-AI

2.  Create virtual environment\
    python -m venv venv

3.  Activate environment\
    Windows: venv`\Scripts`{=tex}`\activate  `{=tex} macOS/Linux: source
    venv/bin/activate

4.  Install dependencies\
    pip install -r backend/requirements.txt

5.  Setup Piper manually inside backend/voice/piper/\
    Required files:

    -   piper.exe
    -   espeak-ng-data/
    -   en_US-danny-low.onnx
    -   en_US-danny-low.onnx.json

------------------------------------------------------------------------

## ▶️ Running the Backend

uvicorn backend.app:app --reload

Open: http://127.0.0.1:8000/ http://127.0.0.1:8000/docs

------------------------------------------------------------------------

## 🎤 Voice Test

Use: POST /api/voice/test

Flow: Microphone → Whisper → Text → Piper → Spoken Response

------------------------------------------------------------------------

## 📌 Project Status

✔ Voice Input Module -- Completed\
✔ Offline STT & TTS -- Completed\
🟡 Intent Detection -- In Progress\
🟡 Desktop App -- Planned

------------------------------------------------------------------------

## 📜 License

Academic and educational use only.
