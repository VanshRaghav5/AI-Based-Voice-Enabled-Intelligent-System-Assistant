from backend.utils.assistant_config import assistant_config


class PersonaEngine:

    def __init__(self, mode: str = None, user_title: str = None):
        self.mode = "butler"
        self.user_title = "sir"
        self.personas = {}
        self.reload(mode=mode, user_title=user_title)

    def reload(self, mode: str = None, user_title: str = None):
        assistant_config.reload()
        config_mode = assistant_config.get("assistant.active_persona", "butler")
        config_title = assistant_config.get("assistant.user_title", "sir")
        config_personas = assistant_config.get("personas", {})

        self.mode = (mode or config_mode or "butler").lower().strip()
        self.user_title = (user_title or config_title or "sir").strip()
        self.personas = config_personas if isinstance(config_personas, dict) else {}

    def _address(self) -> str:
        return self.user_title or "there"

    def _profile(self) -> dict:
        profile = self.personas.get(self.mode)
        if profile:
            return profile
        return {
            "greeting_prefix": "Understood",
            "success_prefix": "Done",
            "error_prefix": "Error",
            "confirmation_prefix": "Confirmation required",
            "cancel_prefix": "Cancelled",
            "shutdown_template": "Shutting down.",
            "interrupted_template": "Interrupted.",
            "error_template": "An error occurred.",
            "confirmation_instruction_template": "Say yes to proceed, or no to cancel.",
        }

    def stylize_response(self, message: str, status: str = "info") -> str:
        clean = (message or "").strip() or "Your request has been processed."
        profile = self._profile()
        status_key = (status or "info").lower().strip()

        if status_key in {"error", "failed"}:
            prefix = profile.get("error_prefix", "Error")
            return f"{prefix}, {self._address()}. {clean}"

        if status_key in {"confirmation_required"}:
            prefix = profile.get("confirmation_prefix", "Confirmation required")
            return f"{prefix}, {self._address()}. {clean}"

        if status_key in {"cancelled", "canceled"}:
            prefix = profile.get("cancel_prefix", "Cancelled")
            return f"{prefix}, {self._address()}. {clean}"

        success_tokens = ["opening", "launched", "created", "set to", "increased", "decreased", "completed", "done"]
        if any(token in clean.lower() for token in success_tokens):
            prefix = profile.get("success_prefix", "Done")
            return f"{prefix}, {self._address()}. {clean}"

        prefix = profile.get("greeting_prefix", "Understood")
        return f"{prefix}, {self._address()}. {clean}"

    def confirmation_instruction(self) -> str:
        template = self._profile().get("confirmation_instruction_template", "Say yes to proceed, or no to cancel.")
        return template.format(title=self._address())

    def shutdown_message(self) -> str:
        template = self._profile().get("shutdown_template", "Shutting down.")
        return template.format(title=self._address())

    def interrupted_message(self) -> str:
        template = self._profile().get("interrupted_template", "Interrupted.")
        return template.format(title=self._address())

    def error_message(self) -> str:
        template = self._profile().get("error_template", "An error occurred.")
        return template.format(title=self._address())


persona = PersonaEngine()
