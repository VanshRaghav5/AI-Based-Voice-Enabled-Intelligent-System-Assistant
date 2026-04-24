from __future__ import annotations

import os
import socket
import subprocess
import tempfile
import threading
import urllib.request
import uuid
from pathlib import Path

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd


class OfflineVoiceBridge:
    """Local-only voice I/O bridge used when internet is unavailable."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self._stt_lock = threading.Lock()
        self._stt_backend = None
        self._stt_model = None

        piper_dir = self.base_dir / "voice" / "tts" / "piper"
        self.piper_exe = piper_dir / "piper.exe"
        self.espeak_data = piper_dir / "espeak-ng-data"
        self.piper_model = piper_dir / "en_US-danny-low.onnx"
        self.piper_config = piper_dir / "en_US-danny-low.onnx.json"

    @staticmethod
    def has_internet(timeout: float = 1.2) -> bool:
        """Best-effort connectivity check that avoids DNS-port false negatives."""
        tcp_targets = (
            ("1.1.1.1", 443),
            ("8.8.8.8", 443),
            ("generativelanguage.googleapis.com", 443),
        )
        for host, port in tcp_targets:
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except OSError:
                continue

        # HTTPS probes for networks that block some raw socket paths.
        http_targets = (
            "https://clients3.google.com/generate_204",
            "https://www.msftconnecttest.com/connecttest.txt",
        )
        for url in http_targets:
            try:
                with urllib.request.urlopen(url, timeout=timeout + 1.0) as resp:
                    if int(getattr(resp, "status", 0) or 0) in (200, 204):
                        return True
            except Exception:
                continue

        return False

    def _ensure_stt(self) -> bool:
        if self._stt_backend is not None:
            return True

        with self._stt_lock:
            if self._stt_backend is not None:
                return True

            try:
                from faster_whisper import WhisperModel  # type: ignore

                self._stt_model = WhisperModel("small", device="cpu", compute_type="int8")
                self._stt_backend = "faster-whisper"
                return True
            except Exception:
                pass

            try:
                import whisper  # type: ignore

                self._stt_model = whisper.load_model("base", device="cpu")
                self._stt_backend = "whisper"
                return True
            except Exception:
                self._stt_backend = "unavailable"
                self._stt_model = None
                return False

    def record_once(self, duration: float = 4.0, sample_rate: int = 16000) -> str:
        """Capture one short voice chunk and return temporary wav path."""
        frames = int(duration * sample_rate)
        audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="int16")
        sd.wait()

        temp_path = Path(tempfile.gettempdir()) / f"omini_offline_{uuid.uuid4().hex[:10]}.wav"
        wav.write(str(temp_path), sample_rate, audio)
        return str(temp_path)

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe local audio with best available local engine."""
        if not self._ensure_stt() or self._stt_model is None:
            return ""

        if self._stt_backend == "faster-whisper":
            segments, _ = self._stt_model.transcribe(
                audio_path,
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
                temperature=0.0,
                language="en",
            )
            text = "".join(seg.text for seg in segments).strip()
            return text

        if self._stt_backend == "whisper":
            result = self._stt_model.transcribe(
                audio_path,
                fp16=False,
                language="en",
                temperature=0.0,
                condition_on_previous_text=False,
            )
            return str(result.get("text", "")).strip()

        return ""

    def listen_and_transcribe_once(self) -> str:
        path = ""
        try:
            path = self.record_once()
            return self.transcribe_file(path)
        finally:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def speak(self, text: str) -> bool:
        """Speak text using local Piper TTS. Returns False if unavailable."""
        clean_text = str(text or "").strip()
        if not clean_text:
            return False

        if not self.piper_exe.exists() or not self.piper_model.exists():
            return False

        out_path = Path(tempfile.gettempdir()) / f"omini_tts_{uuid.uuid4().hex[:10]}.wav"
        cmd = [
            str(self.piper_exe),
            "--model",
            str(self.piper_model),
            "--config",
            str(self.piper_config),
            "--output_file",
            str(out_path),
            "--espeak_data",
            str(self.espeak_data),
        ]

        try:
            subprocess.run(
                cmd,
                cwd=str(self.piper_exe.parent),
                input=clean_text,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=25,
                check=False,
            )
            if not out_path.exists():
                return False

            rate, audio = wav.read(str(out_path))
            sd.play(audio, rate)
            sd.wait()
            return True
        except Exception:
            return False
        finally:
            if out_path.exists():
                try:
                    out_path.unlink()
                except OSError:
                    pass
