import subprocess
import os
import uuid
import sounddevice as sd
import scipy.io.wavfile as wav
from collections import defaultdict

from backend.utils.settings import (
    TTS_LENGTH_SCALE,
    TTS_NOISE_SCALE,
    TTS_NOISE_W,
    TTS_TIMEOUT_SECONDS,
    TTS_ACTIVE_VOICE,
    TTS_ACTIVE_ACCENT,
    TTS_ALLOW_ACCENT_FALLBACK,
    TTS_VOICE_CATALOG,
)
from backend.utils.assistant_config import assistant_config
from backend.utils.logger import logger


BASE_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
AUDIO_OUTPUT_DIR = os.path.join(BACKEND_ROOT, "data", "audio")

PIPER_DIR = os.path.join(BASE_DIR, "piper")
PIPER_EXE = os.path.join(PIPER_DIR, "piper.exe")
ESPEAK_DATA = os.path.join(PIPER_DIR, "espeak-ng-data")

DEFAULT_MODEL_FILE = "en_US-danny-low.onnx"
DEFAULT_CONFIG_FILE = "en_US-danny-low.onnx.json"

os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)


def _model_key_to_voice_name(model_filename: str) -> str:
    """Convert Piper model filename to stable voice key."""
    base = os.path.splitext(os.path.basename(model_filename))[0]
    parts = base.split("-")
    return parts[1].lower() if len(parts) >= 2 else base.lower()


def _model_key_to_accent(model_filename: str) -> str:
    """Extract accent tag from Piper model filename."""
    base = os.path.splitext(os.path.basename(model_filename))[0]
    return base.split("-")[0] if "-" in base else "default"


def _discover_voice_catalog() -> dict:
    """Discover available voices from config and local Piper model files."""
    catalog: dict[str, dict[str, str]] = defaultdict(dict)

    runtime_catalog = assistant_config.get("tts.voice_catalog", TTS_VOICE_CATALOG)
    configured_catalog = runtime_catalog if isinstance(runtime_catalog, dict) else {}
    for accent, accent_voices in configured_catalog.items():
        if not isinstance(accent_voices, dict):
            continue
        for voice_name, model_file in accent_voices.items():
            if not model_file:
                continue
            catalog[str(accent)][str(voice_name).lower()] = str(model_file)

    try:
        for filename in os.listdir(PIPER_DIR):
            if not filename.lower().endswith(".onnx"):
                continue
            model_path = os.path.join(PIPER_DIR, filename)
            if not os.path.isfile(model_path):
                continue
            accent = _model_key_to_accent(filename)
            voice_name = _model_key_to_voice_name(filename)
            catalog[accent][voice_name] = filename
    except FileNotFoundError:
        logger.warning("[TTS] Piper directory not found while discovering voices")

    # Guarantee a default route.
    catalog.setdefault("en_US", {}).setdefault("danny", DEFAULT_MODEL_FILE)
    return dict(catalog)


def get_available_voices() -> dict:
    """Return available voices grouped by accent with file availability info."""
    catalog = _discover_voice_catalog()
    available = {}
    for accent, voices in catalog.items():
        available[accent] = {}
        for voice_name, model_file in voices.items():
            model_path = os.path.join(PIPER_DIR, model_file)
            available[accent][voice_name] = {
                "model": model_file,
                "installed": os.path.exists(model_path),
            }
    return available


def _resolve_voice_model(voice: str | None = None, accent: str | None = None) -> tuple[str, str, str, str]:
    """Resolve model/config paths for requested voice and accent with safe fallback."""
    catalog = _discover_voice_catalog()

    active_voice = str(assistant_config.get("tts.active_voice", TTS_ACTIVE_VOICE)).strip()
    active_accent = str(assistant_config.get("tts.active_accent", TTS_ACTIVE_ACCENT)).strip()
    allow_fallback = bool(assistant_config.get("tts.allow_accent_fallback", TTS_ALLOW_ACCENT_FALLBACK))

    desired_voice = (voice or active_voice or "danny").strip().lower()
    desired_accent = (accent or active_accent or "en_US").strip()

    model_file = catalog.get(desired_accent, {}).get(desired_voice)

    if not model_file and allow_fallback:
        for accent_key, voices in catalog.items():
            if desired_voice in voices:
                model_file = voices[desired_voice]
                desired_accent = accent_key
                break

    if not model_file:
        model_file = catalog.get("en_US", {}).get("danny", DEFAULT_MODEL_FILE)
        desired_voice = _model_key_to_voice_name(model_file)
        desired_accent = _model_key_to_accent(model_file)

    model_path = os.path.join(PIPER_DIR, model_file)
    config_path = f"{model_path}.json"

    if not os.path.exists(model_path):
        logger.warning(
            f"[TTS] Requested voice model missing ({model_file}); using built-in default"
        )
        model_path = os.path.join(PIPER_DIR, DEFAULT_MODEL_FILE)
        config_path = os.path.join(PIPER_DIR, DEFAULT_CONFIG_FILE)
        desired_voice = "danny"
        desired_accent = "en_US"

    if not os.path.exists(config_path):
        # Piper can often run without an explicit config; keep CLI stable by passing best-effort path.
        config_path = f"{model_path}.json"

    return model_path, config_path, desired_voice, desired_accent


def speak_text(text: str, voice: str | None = None, accent: str | None = None) -> str:

    if not str(text or "").strip():
        logger.debug("[TTS] Empty text provided; skipping synthesis")
        return ""

    if not os.path.exists(PIPER_EXE):
        logger.error("[TTS Error] Piper executable not found.")
        return ""

    try:
        model_path, config_path, resolved_voice, resolved_accent = _resolve_voice_model(
            voice=voice,
            accent=accent,
        )

        output_file = os.path.join(
            AUDIO_OUTPUT_DIR,
            f"{uuid.uuid4()}.wav"
        )

        command = [
            PIPER_EXE,
            "--model", model_path,
            "--config", config_path,
            "--output_file", output_file,
            "--espeak_data", ESPEAK_DATA,
            "--length_scale", str(TTS_LENGTH_SCALE),
            "--noise_scale", str(TTS_NOISE_SCALE),
            "--noise_w", str(TTS_NOISE_W)
        ]

        logger.info(
            f"Running Piper TTS (voice={resolved_voice}, accent={resolved_accent})..."
        )

        subprocess.run(
            command,
            cwd=PIPER_DIR,
            input=text,
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TTS_TIMEOUT_SECONDS
        )

        rate, audio = wav.read(output_file)
        sd.play(audio, rate)
        sd.wait()

        if os.path.exists(output_file):
            os.remove(output_file)

        logger.info("TTS playback completed")

        return "success"

    except subprocess.TimeoutExpired:
        logger.error("[TTS Error] Piper timed out.")
        return ""

    except Exception as e:
        logger.error(f"[TTS Error] {e}")
        return ""
