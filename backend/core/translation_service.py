"""Language translation helpers for multi-language command processing."""

import time
from typing import Tuple

from backend.config.assistant_config import assistant_config
from backend.config.logger import logger

try:
    from deep_translator import GoogleTranslator
except Exception:  # pragma: no cover - optional dependency fallback
    GoogleTranslator = None


LANGUAGE_ALIASES = {
    "en": "en",
    "english": "en",
    "hi": "hi",
    "hindi": "hi",
    "hinglish": "hi",
    "es": "es",
    "spanish": "es",
    "fr": "fr",
    "french": "fr",
    "de": "de",
    "german": "de",
}


class TranslationService:
    """Translate commands to English and responses to the selected language."""

    def __init__(self):
        self.enabled = GoogleTranslator is not None
        self.cache_ttl_seconds = float(assistant_config.get("translation.cache_ttl_seconds", 30))
        self.cache_max_entries = int(assistant_config.get("translation.cache_max_entries", 512))
        self._translation_cache = {}
        self._translator_pool = {}
        if not self.enabled:
            logger.warning("[Translation] deep-translator not installed, running without translation")

    def _build_cache_key(self, source: str, target: str, text: str) -> str:
        normalized_text = str(text or "").strip()
        if not normalized_text:
            return ""
        return f"{source}->{target}::{normalized_text.lower()}"

    def _get_cached_translation(self, source: str, target: str, text: str):
        if self.cache_ttl_seconds <= 0:
            return None

        cache_key = self._build_cache_key(source, target, text)
        if not cache_key:
            return None

        cached = self._translation_cache.get(cache_key)
        if not cached:
            return None

        if cached.get("expires_at", 0.0) < time.time():
            self._translation_cache.pop(cache_key, None)
            return None

        return str(cached.get("value", "") or "")

    def _store_translation_cache(self, source: str, target: str, text: str, translated: str) -> None:
        if self.cache_ttl_seconds <= 0 or self.cache_max_entries <= 0:
            return

        cache_key = self._build_cache_key(source, target, text)
        if not cache_key:
            return

        self._translation_cache[cache_key] = {
            "value": str(translated or ""),
            "expires_at": time.time() + self.cache_ttl_seconds,
        }

        while len(self._translation_cache) > self.cache_max_entries:
            oldest_key = next(iter(self._translation_cache))
            self._translation_cache.pop(oldest_key, None)

    def _get_translator(self, source: str, target: str):
        key = f"{source}->{target}"
        translator = self._translator_pool.get(key)
        if translator is not None:
            return translator

        translator = GoogleTranslator(source=source, target=target)
        self._translator_pool[key] = translator
        return translator

    @staticmethod
    def normalize_language(language: str) -> str:
        if not language:
            return "en"
        return LANGUAGE_ALIASES.get(str(language).strip().lower(), "en")

    def translate_command_to_english(self, text: str, language: str) -> Tuple[str, bool]:
        """Translate incoming user command to English for parser/LLM execution."""
        target_lang = self.normalize_language(language)
        if not self.enabled or target_lang == "en" or not text:
            return text, False

        cached = self._get_cached_translation("auto", "en", text)
        if cached:
            return cached, cached.strip().lower() != text.strip().lower()

        try:
            translated = self._get_translator("auto", "en").translate(text)
            if translated and translated.strip():
                value = translated.strip()
                self._store_translation_cache("auto", "en", text, value)
                return value, value.lower() != text.strip().lower()
        except Exception as exc:
            logger.warning(f"[Translation] Command translation failed: {exc}")

        return text, False

    def translate_response_from_english(self, text: str, language: str) -> Tuple[str, bool]:
        """Translate English response text to the preferred output language."""
        target_lang = self.normalize_language(language)
        # Keep hinglish output in English text to avoid script mismatch in current UI.
        if str(language).strip().lower() == "hinglish":
            target_lang = "en"

        if not self.enabled or target_lang == "en" or not text:
            return text, False

        cached = self._get_cached_translation("auto", target_lang, text)
        if cached:
            return cached, cached.strip().lower() != text.strip().lower()

        try:
            translated = self._get_translator("auto", target_lang).translate(text)
            if translated and translated.strip():
                value = translated.strip()
                self._store_translation_cache("auto", target_lang, text, value)
                return value, value.lower() != text.strip().lower()
        except Exception as exc:
            logger.warning(f"[Translation] Response translation failed: {exc}")

        return text, False
