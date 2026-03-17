import os
import re


class ResponseFormatter:
    """Convert raw tool results into clearer user-facing responses."""

    def format(self, result: dict) -> dict:
        """Return a copy of the result with a clearer message."""
        if not isinstance(result, dict):
            return result

        formatted = dict(result)
        status = str(formatted.get("status", "info")).strip().lower()
        message = str(formatted.get("message", "") or "").strip()
        data = formatted.get("data") if isinstance(formatted.get("data"), dict) else {}

        if status == "success":
            formatted["message"] = self._format_success(message, data)
        elif status in {"error", "failed"}:
            formatted["message"] = self._format_error(message, data)
        elif status == "confirmation_required":
            formatted["message"] = self._format_confirmation(message, data)
        elif status in {"cancelled", "canceled"}:
            formatted["message"] = self._format_cancelled(message)
        else:
            formatted["message"] = self._cleanup(message or "Your request has been processed.")

        return formatted

    def _format_success(self, message: str, data: dict) -> str:
        clean = self._cleanup(message)
        lowered = clean.lower()

        url = str(data.get("url", "") or "")
        if "youtube.com/watch" in url:
            return "I opened the latest YouTube video."
        if "youtube.com/results" in url:
            query = data.get("query")
            if query:
                return f"I opened YouTube results for {query}."
            return "I opened YouTube search results."

        if lowered.startswith("opening "):
            target = clean[8:].strip()
            if target:
                return f"I am opening {target}."

        if lowered.startswith("opened "):
            target = clean[7:].strip()
            if target:
                return f"I opened {target}."

        if lowered.startswith("searching google for"):
            query = data.get("query") or clean[len("Searching Google for"):].strip().strip("'\"")
            return f"I searched Google for {query}." if query else "I opened a Google search in your browser."

        if clean.lower().startswith("file created:"):
            filename = clean.split(":", 1)[1].strip()
            return f"I created the file {filename}."

        if clean.lower().startswith("moved ") and "recycle bin" in clean.lower():
            path = data.get("path") or clean.split(" to Recycle Bin", 1)[0].replace("Moved ", "", 1).strip()
            item_name = os.path.basename(path) or path
            return f"I moved {item_name} to the Recycle Bin. It can still be restored."

        if clean.lower().startswith("file moved successfully to"):
            destination = data.get("destination") or clean.split("to", 1)[1].strip()
            item_name = os.path.basename(destination) or destination
            return f"I moved the file to {item_name}."

        if clean.lower().startswith("volume increased by"):
            return self._sentence_case("I increased the volume " + clean[len("Volume increased"):].strip())

        if clean.lower().startswith("volume decreased by"):
            return self._sentence_case("I decreased the volume " + clean[len("Volume decreased"):].strip())

        if clean.lower() == "volume mute toggled":
            return "I toggled mute for the system volume."

        if clean.lower() == "command completed":
            return "I completed your request."

        return self._ensure_sentence(clean)

    def _format_error(self, message: str, data: dict) -> str:
        clean = self._cleanup(message)
        lowered = clean.lower()

        if not clean or lowered == "execution failed.":
            return "I could not complete that request."

        if lowered == "i did not understand that command.":
            return "I could not understand that command. Please try again with a shorter or more specific instruction."

        if lowered == "no pending action to confirm":
            return "There is no action waiting for confirmation right now."

        if lowered.startswith("tool ") and lowered.endswith(" not found"):
            return "I could not complete that request because the required action is not available."

        if lowered == "file not found":
            return "I could not find that file. Please check the path and try again."

        return self._ensure_sentence(clean)

    def _format_confirmation(self, message: str, data: dict) -> str:
        clean = self._cleanup(message or "Please confirm this action.")
        lowered = clean.lower()
        if "say yes to proceed" in lowered or "say no to cancel" in lowered:
            return self._ensure_sentence(clean)
        return f"{self._ensure_sentence(clean)} Say yes to proceed or no to cancel."

    def _format_cancelled(self, message: str) -> str:
        clean = self._cleanup(message)
        if not clean or clean.lower() == "operation cancelled by user":
            return "I cancelled that action."
        return self._ensure_sentence(clean)

    @staticmethod
    def _cleanup(message: str) -> str:
        return re.sub(r"\s+", " ", str(message or "")).strip()

    def _ensure_sentence(self, message: str) -> str:
        clean = self._cleanup(message)
        if not clean:
            return "Your request has been processed."
        if clean[-1] not in ".!?":
            clean = f"{clean}."
        return clean[0].upper() + clean[1:]

    def _sentence_case(self, message: str) -> str:
        clean = self._ensure_sentence(message)
        return clean[0].upper() + clean[1:]