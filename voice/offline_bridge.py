from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import tempfile
import threading
import urllib.request
import uuid
from pathlib import Path

import numpy as np
import requests
import scipy.io.wavfile as wav
import sounddevice as sd

try:
    from core.voice_manager import get_voice_manager
except Exception:
    get_voice_manager = None


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
        self.ollama_base_url = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_0")

        if get_voice_manager is not None:
            try:
                self.set_voice_key(get_voice_manager().get_selected_key())
            except Exception:
                pass

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

    def ollama_available(self, timeout: float = 1.0) -> bool:
        try:
            resp = requests.get(f"{self.ollama_base_url}/api/tags", timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False

    def ask_ollama(self, user_text: str, system_prompt: str = "", timeout: float = 45.0) -> str:
        text = str(user_text or "").strip()
        if not text:
            return ""

        messages = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": text})

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        try:
            resp = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json=payload,
                timeout=timeout,
            )
            if resp.status_code != 200:
                return ""

            data = resp.json() if resp.content else {}
            msg = data.get("message") if isinstance(data, dict) else None
            content = msg.get("content", "") if isinstance(msg, dict) else ""
            return str(content or "").strip()
        except Exception:
            return ""

    @staticmethod
    def _extract_json_object(text: str) -> dict | None:
        raw = str(text or "").strip()
        if not raw:
            return None

        # Try direct JSON first.
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            pass

        # Fallback: first JSON object block in model output.
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def plan_offline_turn(
        self,
        user_text: str,
        *,
        allowed_tools: list[str],
        system_prompt: str = "",
        timeout: float = 35.0,
    ) -> dict:
        text = str(user_text or "").strip()
        if not text:
            return {"mode": "respond", "reply": ""}

        tools_csv = ", ".join(allowed_tools)
        planner_prompt = (
            f"{system_prompt}\n\n"
            "You are an offline command router. "
            "Decide whether to answer directly or call one local tool. "
            f"Allowed tools: {tools_csv}. "
            "Return ONLY valid JSON with this schema: "
            "{\"mode\":\"respond|tool\",\"reply\":\"...\",\"tool_name\":\"...\",\"args\":{}}. "
            "If mode is tool, include tool_name and args; reply may be short confirmation text. "
            "If mode is respond, include reply and leave tool_name empty and args as {}."
        )

        model_out = self.ask_ollama(text, system_prompt=planner_prompt, timeout=timeout)
        parsed = self._extract_json_object(model_out)
        if not parsed:
            return {"mode": "respond", "reply": model_out or "", "tool_name": "", "args": {}}

        mode = str(parsed.get("mode", "respond")).strip().lower()
        if mode not in {"respond", "tool"}:
            mode = "respond"

        tool_name = str(parsed.get("tool_name", "")).strip()
        args = parsed.get("args", {})
        if not isinstance(args, dict):
            args = {}

        reply = str(parsed.get("reply", "")).strip()

        if mode == "tool" and tool_name not in allowed_tools:
            # Safety fallback if model proposes non-allowed tool.
            return {
                "mode": "respond",
                "reply": reply or "I cannot run that action offline.",
                "tool_name": "",
                "args": {},
            }

        return {
            "mode": mode,
            "reply": reply,
            "tool_name": tool_name,
            "args": args,
        }

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

    def set_voice_model(self, model_file: str) -> bool:
        model = str(model_file or "").strip()
        if not model:
            return False

        piper_dir = self.base_dir / "voice" / "tts" / "piper"
        model_path = piper_dir / model
        config_path = Path(f"{model_path}.json")

        if not model_path.exists():
            return False

        self.piper_model = model_path
        self.piper_config = config_path if config_path.exists() else Path(f"{model_path}.json")
        return True

    def set_voice_key(self, key: str) -> bool:
        if get_voice_manager is None:
            return False

        try:
            manager = get_voice_manager()
            profile = manager.set_selected_key(key)
            return self.set_voice_model(profile.model_file)
        except Exception:
            return False

    def get_voice_key(self) -> str:
        if get_voice_manager is None:
            return Path(self.piper_model).stem.lower()

        try:
            return get_voice_manager().get_selected_key()
        except Exception:
            return Path(self.piper_model).stem.lower()

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
