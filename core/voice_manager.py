from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _get_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent


BASE_DIR = _get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "voice.json"
PIPER_DIR = BASE_DIR / "voice" / "tts" / "piper"
LIVE_CONFIG_PATH = BASE_DIR / "config" / "live_voice.json"


@dataclass(frozen=True)
class VoiceProfile:
    key: str
    title: str
    model_file: str
    accent: str


@dataclass(frozen=True)
class LiveVoiceProfile:
    key: str
    title: str


def _title_from_model(model_file: str) -> str:
    stem = Path(model_file).stem
    parts = stem.split("-")
    if len(parts) >= 2:
        return parts[1].replace("_", " ").title()
    return stem.replace("_", " ").title()


def _accent_from_model(model_file: str) -> str:
    stem = Path(model_file).stem
    return stem.split("-")[0] if "-" in stem else "en_US"


def discover_voice_profiles() -> dict[str, VoiceProfile]:
    voices: dict[str, VoiceProfile] = {}
    if not PIPER_DIR.exists():
        return voices

    for model_path in sorted(PIPER_DIR.glob("*.onnx")):
        model_file = model_path.name
        key = model_path.stem.lower()
        voices[key] = VoiceProfile(
            key=key,
            title=_title_from_model(model_file),
            model_file=model_file,
            accent=_accent_from_model(model_file),
        )

    if not voices:
        default_model = "en_US-danny-low.onnx"
        voices[Path(default_model).stem.lower()] = VoiceProfile(
            key=Path(default_model).stem.lower(),
            title="Danny",
            model_file=default_model,
            accent="en_US",
        )

    return voices


def _default_config() -> dict[str, Any]:
    profiles = discover_voice_profiles()
    default_key = next(iter(profiles)) if profiles else "en_us-danny-low"
    return {
        "voice": default_key,
    }


class VoiceManager:
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._voices = discover_voice_profiles()
        self._config = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            cfg = _default_config()
            self._save(cfg)
            return cfg
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("voice config must be an object")
            merged = _default_config()
            merged.update({k: v for k, v in data.items() if v is not None})
            if merged.get("voice") not in self._voices:
                merged["voice"] = next(iter(self._voices)) if self._voices else "en_us-danny-low"
            return merged
        except Exception:
            cfg = _default_config()
            self._save(cfg)
            return cfg

    def _save(self, data: dict[str, Any]) -> None:
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_profiles(self) -> list[VoiceProfile]:
        return list(self._voices.values())

    def get_selected_key(self) -> str:
        return str(self._config.get("voice", next(iter(self._voices), "en_us-danny-low")))

    def get_selected_profile(self) -> VoiceProfile:
        key = self.get_selected_key()
        return self._voices.get(key, next(iter(self._voices.values())))

    def set_selected_key(self, key: str) -> VoiceProfile:
        if key not in self._voices:
            key = next(iter(self._voices), "en_us-danny-low")
        self._config["voice"] = key
        self._save(self._config)
        return self._voices[key]


_GLOBAL_VOICES: VoiceManager | None = None


def get_voice_manager() -> VoiceManager:
    global _GLOBAL_VOICES
    if _GLOBAL_VOICES is None:
        _GLOBAL_VOICES = VoiceManager()
    return _GLOBAL_VOICES


def list_voices() -> list[VoiceProfile]:
    return get_voice_manager().list_profiles()


LIVE_VOICES: dict[str, LiveVoiceProfile] = {
    "Charon": LiveVoiceProfile(key="Charon", title="Charon"),
    "Aoede": LiveVoiceProfile(key="Aoede", title="Aoede"),
    "Kore": LiveVoiceProfile(key="Kore", title="Kore"),
    "Fenrir": LiveVoiceProfile(key="Fenrir", title="Fenrir"),
    "Puck": LiveVoiceProfile(key="Puck", title="Puck"),
    "Zephyr": LiveVoiceProfile(key="Zephyr", title="Zephyr"),
    "Leda": LiveVoiceProfile(key="Leda", title="Leda"),
    "Orus": LiveVoiceProfile(key="Orus", title="Orus"),
}


def _default_live_config() -> dict[str, Any]:
    return {"voice": "Charon"}


class LiveVoiceManager:
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or LIVE_CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            cfg = _default_live_config()
            self._save(cfg)
            return cfg
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("live voice config must be an object")
            merged = _default_live_config()
            merged.update({k: v for k, v in data.items() if v is not None})
            if merged.get("voice") not in LIVE_VOICES:
                merged["voice"] = "Charon"
            return merged
        except Exception:
            cfg = _default_live_config()
            self._save(cfg)
            return cfg

    def _save(self, data: dict[str, Any]) -> None:
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_profiles(self) -> list[LiveVoiceProfile]:
        return list(LIVE_VOICES.values())

    def get_selected_key(self) -> str:
        return str(self._config.get("voice", "Charon"))

    def get_selected_profile(self) -> LiveVoiceProfile:
        return LIVE_VOICES.get(self.get_selected_key(), LIVE_VOICES["Charon"])

    def set_selected_key(self, key: str) -> LiveVoiceProfile:
        if key not in LIVE_VOICES:
            key = "Charon"
        self._config["voice"] = key
        self._save(self._config)
        return LIVE_VOICES[key]


_GLOBAL_LIVE_VOICES: LiveVoiceManager | None = None


def get_live_voice_manager() -> LiveVoiceManager:
    global _GLOBAL_LIVE_VOICES
    if _GLOBAL_LIVE_VOICES is None:
        _GLOBAL_LIVE_VOICES = LiveVoiceManager()
    return _GLOBAL_LIVE_VOICES


def list_live_voices() -> list[LiveVoiceProfile]:
    return get_live_voice_manager().list_profiles()