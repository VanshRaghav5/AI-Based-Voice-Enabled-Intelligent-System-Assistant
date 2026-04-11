"""Rule-based intent classifier for the planning layer."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

from backend.utils.logger import log
from backend.utils.settings import LLM_MODEL, LLM_TIMEOUT_SECONDS


@dataclass(frozen=True)
class IntentRule:
    """Simple keyword rule used to detect an intent."""

    intent: str
    keywords: List[str]
    confidence: float
    match_all: bool = False


class IntentClassifier:
    """Basic rule-based intent classifier.

    This is intentionally lightweight so the planning layer can start with
    predictable behavior before an LLM-based classifier is added.
    """

    def __init__(self) -> None:
        self._llm_intent_enabled = str(os.getenv("LLM_INTENT_CLASSIFICATION", "")).lower() in {"1", "true", "yes"}
        self._rules = [
            IntentRule(
                intent="continue_work",
                keywords=["continue my work", "continue work", "resume work", "resume my work"],
                confidence=0.9,
            ),
            IntentRule(
                intent="open_project",
                keywords=["open my project", "open project", "load project", "go to project"],
                confidence=0.88,
            ),
            IntentRule(
                intent="start_work_session",
                keywords=["start", "work", "work session", "focus mode", "begin work", "start working"],
                confidence=0.9,
                match_all=True,
            ),
            IntentRule(
                intent="organize_files",
                keywords=["organize", "sort files", "tidy files", "clean folder", "arrange files"],
                confidence=0.85,
            ),
            IntentRule(
                intent="run_command",
                keywords=["run", "execute", "terminal", "shell", "command"],
                confidence=0.8,
            ),
            IntentRule(
                intent="open_app",
                keywords=["open", "launch", "start app", "run app"],
                confidence=0.8,
            ),
            IntentRule(
                intent="search_web",
                keywords=["search", "google", "look up", "find online", "search web"],
                confidence=0.82,
            ),
        ]

    def classify(self, user_input: str, use_llm: bool | None = None) -> Dict[str, object]:
        """Classify a user request into a high-level intent."""
        text = (user_input or "").strip().lower()
        llm_enabled = self._llm_intent_enabled if use_llm is None else bool(use_llm)

        if not text:
            log(f"Classifier: Empty input, returning unknown intent")
            return {"intent": "unknown", "confidence": 0.5, "matched_keywords": []}

        for rule in self._rules:
            matched_keywords = [keyword for keyword in rule.keywords if keyword in text]
            if rule.match_all:
                required_keywords = [keyword for keyword in rule.keywords if len(keyword.split()) == 1]
                if required_keywords and all(keyword in text for keyword in required_keywords):
                    log(f"Classifier: Matched '{rule.intent}' (confidence: {rule.confidence}) with keywords {required_keywords}")
                    return {
                        "intent": rule.intent,
                        "confidence": rule.confidence,
                        "matched_keywords": required_keywords,
                    }

            if matched_keywords:
                log(f"Classifier: Matched '{rule.intent}' (confidence: {rule.confidence}) with keywords {matched_keywords}")
                return {
                    "intent": rule.intent,
                    "confidence": rule.confidence,
                    "matched_keywords": matched_keywords,
                }

        log(f"Classifier: No rules matched, returning unknown intent")
        if llm_enabled:
            llm_result = self._classify_with_llm(user_input)
            if llm_result:
                return llm_result

        return {"intent": "unknown", "confidence": 0.5, "matched_keywords": []}

    def _classify_with_llm(self, user_input: str) -> Optional[Dict[str, object]]:
        prompt = (
            "Classify the user request into one assistant intent. "
            "Return strict JSON with keys intent and confidence. "
            "Allowed intents: start_work_session, organize_files, run_command, open_app, search_web, continue_work, open_project, unknown.\n\n"
            f"User request: {user_input}\n\n"
            'Return JSON like: {"intent": "run_command", "confidence": 0.93}'
        )

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": os.getenv("OLLAMA_MODEL", LLM_MODEL),
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 128},
                },
                timeout=LLM_TIMEOUT_SECONDS,
            )
            if response.status_code != 200:
                return None

            output = response.json().get("response", "").strip()
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", output, re.DOTALL | re.IGNORECASE)
            candidate = match.group(1).strip() if match else output
            payload = json.loads(candidate)
            if not isinstance(payload, dict):
                return None

            intent = str(payload.get("intent", "unknown")).strip() or "unknown"
            confidence = float(payload.get("confidence", 0.5))
            log(f"Classifier: LLM matched '{intent}' (confidence: {confidence})")
            return {"intent": intent, "confidence": confidence, "matched_keywords": [], "source": "llm"}
        except Exception as exc:
            log(f"Classifier: LLM classification failed: {exc}")
            return None