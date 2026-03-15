"""Basic UI translation dictionary for desktop labels and system messages."""

TRANSLATIONS = {
    "english": {
        "type_command_placeholder": "Type your command here...",
        "send": "Send",
        "processing": "Processing...",
        "start_listening": "Start Listening",
        "stop_listening": "Stop Listening",
        "wake_word_on": "Wake Word: ON",
        "wake_word_off": "Wake Word: OFF",
        "connected": "Connected to backend.",
        "connected_ready": "Connected to backend. Ready to assist!",
        "disconnected": "Disconnected from backend.",
        "welcome_message": (
            "Hello! I'm OmniAssist, your AI assistant.\n\n"
            "I can help you with:\n"
            "  - Opening applications\n"
            "  - Web searches and browsing\n"
            "  - System commands\n"
            "  - File management\n"
            "  - Answering questions\n\n"
            "Try saying \"open WhatsApp\" or type your command below!"
        ),
    },
    "hindi": {
        "type_command_placeholder": "Apna command yahan likhiye...",
        "send": "Bheje",
        "processing": "Prakriya chal rahi hai...",
        "start_listening": "Sunna shuru kare",
        "stop_listening": "Sunna band kare",
        "wake_word_on": "Wake Word: Chalu",
        "wake_word_off": "Wake Word: Band",
        "connected": "Backend se jud gaye.",
        "connected_ready": "Backend se jud gaye. Taiyar hoon!",
        "disconnected": "Backend se connection toot gaya.",
        "welcome_message": (
            "Namaste! Main OmniAssist hoon, aapka AI assistant.\n\n"
            "Main in kaamon me madad kar sakta hoon:\n"
            "  - Applications kholna\n"
            "  - Web search aur browsing\n"
            "  - System commands\n"
            "  - File management\n"
            "  - Questions ka jawab\n\n"
            "\"open WhatsApp\" bolkar ya command type karke try karein!"
        ),
    },
    "hinglish": {
        "type_command_placeholder": "Yahan command type karo...",
        "send": "Send",
        "processing": "Process ho raha hai...",
        "start_listening": "Listening Start",
        "stop_listening": "Listening Stop",
        "wake_word_on": "Wake Word: ON",
        "wake_word_off": "Wake Word: OFF",
        "connected": "Backend connected.",
        "connected_ready": "Backend connected. Ready to assist!",
        "disconnected": "Backend disconnected.",
        "welcome_message": (
            "Hi! Main OmniAssist hoon, tumhara AI assistant.\n\n"
            "Main help kar sakta hoon:\n"
            "  - Apps open karna\n"
            "  - Web search aur browsing\n"
            "  - System commands\n"
            "  - File management\n"
            "  - Questions ke answers\n\n"
            "\"open WhatsApp\" bolke ya niche command type karke try karo!"
        ),
    },
}


def tr(key: str, language: str = "english") -> str:
    """Translate a UI key with English fallback."""
    lang = (language or "english").strip().lower()
    selected = TRANSLATIONS.get(lang, TRANSLATIONS["english"])
    return selected.get(key, TRANSLATIONS["english"].get(key, key))
