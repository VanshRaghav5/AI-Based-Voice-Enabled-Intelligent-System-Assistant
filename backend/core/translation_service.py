"""Language translation helpers for multi-language command processing."""

from typing import Tuple

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
        if not self.enabled:
            logger.warning("[Translation] deep-translator not installed, running without translation")

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

        try:
            translated = GoogleTranslator(source="auto", target="en").translate(text)
            if translated and translated.strip():
                return translated.strip(), translated.strip().lower() != text.strip().lower()
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

        try:
            translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
            if translated and translated.strip():
                return translated.strip(), translated.strip().lower() != text.strip().lower()
        except Exception as exc:
            logger.warning(f"[Translation] Response translation failed: {exc}")

        return text, False
