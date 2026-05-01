import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _get_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent


BASE_DIR = _get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "persona.json"


@dataclass(frozen=True)
class PersonaProfile:
    key: str
    title: str
    summary: str
    response_rules: list[str]

    def as_prompt_block(self) -> str:
        rules = "\n".join(f"- {rule}" for rule in self.response_rules)
        return (
            f"[PERSONA: {self.title}]\n"
            f"{self.summary}\n"
            f"Response rules:\n{rules}\n"
        )


PERSONAS: dict[str, PersonaProfile] = {
    "executive": PersonaProfile(
        key="executive",
        title="Executive",
        summary="Fast, precise, and outcome-driven. Prefer short answers, clear next steps, and minimal wording.",
        response_rules=[
            "Lead with the answer.",
            "Keep replies compact unless the user asks for depth.",
            "Avoid filler, hedging, and repeated confirmation language.",
            "Use plain language and clean structure.",
        ],
    ),
    "engineer": PersonaProfile(
        key="engineer",
        title="Engineer",
        summary="Technical, direct, and implementation-focused. Good for debugging, code, and system work.",
        response_rules=[
            "Be explicit about root cause and fix.",
            "Prefer concise technical language.",
            "Call out risks and validation steps.",
            "Avoid casual fluff.",
        ],
    ),
    "calm": PersonaProfile(
        key="calm",
        title="Calm",
        summary="Measured, reassuring, and smooth. Useful for a softer voice without becoming verbose.",
        response_rules=[
            "Stay calm and steady.",
            "Use short, reassuring phrasing.",
            "Never sound abrupt or noisy.",
            "Keep transitions smooth.",
        ],
    ),
    "strategist": PersonaProfile(
        key="strategist",
        title="Strategist",
        summary="High-level, analytical, and action-oriented. Focus on plans, tradeoffs, and best moves.",
        response_rules=[
            "Summarize the goal and best path first.",
            "Include tradeoffs only when relevant.",
            "Stay concise and decisive.",
            "Recommend a next action when useful.",
        ],
    ),
    "minimal": PersonaProfile(
        key="minimal",
        title="Minimal",
        summary="Ultra-compact responses. Best when the user wants the shortest useful answer possible.",
        response_rules=[
            "Use the fewest words needed.",
            "Do not elaborate unless asked.",
            "Prefer one-sentence answers.",
            "Keep formatting minimal.",
        ],
    ),
}


def _default_config() -> dict[str, Any]:
    return {
        "persona": "executive",
        "response_mode": "clean",
    }


class PersonaManager:
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            cfg = _default_config()
            self._save(cfg)
            return cfg
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("persona config must be an object")
            merged = _default_config()
            merged.update({k: v for k, v in data.items() if v is not None})
            if merged.get("persona") not in PERSONAS:
                merged["persona"] = "executive"
            if merged.get("response_mode") not in {"clean", "balanced", "detailed"}:
                merged["response_mode"] = "clean"
            return merged
        except Exception:
            cfg = _default_config()
            self._save(cfg)
            return cfg

    def _save(self, data: dict[str, Any]) -> None:
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_selected_key(self) -> str:
        return str(self._config.get("persona", "executive"))

    def get_selected_profile(self) -> PersonaProfile:
        return PERSONAS.get(self.get_selected_key(), PERSONAS["executive"])

    def set_selected_key(self, key: str) -> PersonaProfile:
        if key not in PERSONAS:
            key = "executive"
        self._config["persona"] = key
        self._save(self._config)
        return PERSONAS[key]

    def get_response_mode(self) -> str:
        return str(self._config.get("response_mode", "clean"))

    def set_response_mode(self, mode: str) -> str:
        if mode not in {"clean", "balanced", "detailed"}:
            mode = "clean"
        self._config["response_mode"] = mode
        self._save(self._config)
        return mode

    def build_prompt_suffix(self) -> str:
        persona = self.get_selected_profile()
        mode = self.get_response_mode()
        mode_rules = {
            "clean": [
                "Prefer short, polished responses.",
                "Avoid repetition and extra framing.",
                "Do not add commentary unless it helps the user act faster.",
            ],
            "balanced": [
                "Be concise by default, but include enough detail to be useful.",
            ],
            "detailed": [
                "Expand when the user asks for explanation, but stay organized.",
            ],
        }
        mode_block = "\n".join(f"- {rule}" for rule in mode_rules.get(mode, []))
        return (
            f"\n{persona.as_prompt_block()}"
            f"Response mode: {mode}\n"
            f"Mode rules:\n{mode_block}\n"
            "Always stay direct, smooth, and clean."
        )


_GLOBAL_PERSONAS: PersonaManager | None = None


def get_persona_manager() -> PersonaManager:
    global _GLOBAL_PERSONAS
    if _GLOBAL_PERSONAS is None:
        _GLOBAL_PERSONAS = PersonaManager()
    return _GLOBAL_PERSONAS


def list_personas() -> list[PersonaProfile]:
    return list(PERSONAS.values())
