import json
import os
import threading
from pathlib import Path
from dataclasses import asdict, fields

from backend.utils.assistant_config import assistant_config
from backend.utils.logger import logger
from backend.core.memory.state_schema import SessionStateSchema


class SessionState:

    def __init__(self):
        self._lock = threading.RLock()
        self._persist_enabled = assistant_config.get("memory.enabled", True)
        self._max_history = int(assistant_config.get("memory.max_history", 200) or 200)

        default_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "data", "session_memory.json")
        )
        configured_path = assistant_config.get("memory.file", default_path)
        if os.path.isabs(configured_path):
            self._memory_file = configured_path
        else:
            project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
            self._memory_file = os.path.normpath(os.path.join(project_root, configured_path))

        self._state = SessionStateSchema()
        self._load_from_disk()

    def _schema_field_names(self):
        return {field.name for field in fields(SessionStateSchema)}

    def _serialize_state(self):
        payload = asdict(self._state)
        payload["execution_history"] = payload.get("execution_history", [])[-self._max_history:]
        return payload

    def _save_to_disk(self):
        if not self._persist_enabled:
            return

        try:
            os.makedirs(os.path.dirname(self._memory_file), exist_ok=True)
            temp_file = f"{self._memory_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as file:
                json.dump(self._serialize_state(), file, ensure_ascii=True, indent=2, default=str)
            os.replace(temp_file, self._memory_file)
        except Exception as exc:
            logger.error(f"[SessionState] Failed to persist memory: {exc}")

    def _load_from_disk(self):
        if not self._persist_enabled:
            logger.info("[SessionState] Persistent memory disabled via config")
            return

        if not os.path.exists(self._memory_file):
            logger.info(f"[SessionState] Memory file not found, starting fresh: {self._memory_file}")
            self._save_to_disk()
            return

        try:
            with open(self._memory_file, "r", encoding="utf-8") as file:
                payload = json.load(file)

            if not isinstance(payload, dict):
                logger.warning("[SessionState] Invalid memory payload format, resetting to defaults")
                self._state = SessionStateSchema()
                self._save_to_disk()
                return

            allowed_fields = self._schema_field_names()
            safe_payload = {key: value for key, value in payload.items() if key in allowed_fields}

            history = safe_payload.get("execution_history", [])
            facts = safe_payload.get("facts", {})

            if not isinstance(history, list):
                history = []
            if not isinstance(facts, dict):
                facts = {}

            safe_payload["execution_history"] = history[-self._max_history:]
            safe_payload["facts"] = {str(k): str(v) for k, v in facts.items()}

            self._state = SessionStateSchema(**safe_payload)
            logger.info(f"[SessionState] Loaded persistent memory from: {self._memory_file}")
        except Exception as exc:
            logger.error(f"[SessionState] Failed to load memory file: {exc}")
            self._state = SessionStateSchema()

    def get_state(self):
        with self._lock:
            return SessionStateSchema(**self._serialize_state())

    def update(self, updates: dict):
        with self._lock:
            for key, value in updates.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)
            self._save_to_disk()

    def _update_context_from_entry(self, entry: dict):
        """Infer useful memory context from tool result payloads."""
        if not isinstance(entry, dict):
            return

        tool_name = str(entry.get("tool_name", "")).strip().lower()
        data = entry.get("data", {}) if isinstance(entry.get("data"), dict) else {}
        args = entry.get("tool_args", {}) if isinstance(entry.get("tool_args"), dict) else {}

        path = data.get("path") or args.get("path") or args.get("source") or data.get("source")
        cwd = data.get("cwd") or args.get("cwd")
        url = data.get("url") or args.get("url")
        contact = (
            data.get("recipient")
            or data.get("target")
            or args.get("recipient")
            or args.get("target")
        )

        file_or_folder_tools = {
            "create_file",
            "write_file",
            "read_file",
            "move_file",
            "delete_file",
            "open_project",
            "list_directory",
            "search_files",
            "run_command",
        }

        if path and (tool_name in file_or_folder_tools or os.path.sep in str(path) or ":\\" in str(path)):
            path_str = str(path)
            self._state.last_file_path = path_str
            try:
                candidate = Path(path_str).expanduser()
                if candidate.suffix:
                    self._state.last_folder_path = str(candidate.parent)
                else:
                    self._state.last_folder_path = str(candidate)
            except Exception:
                pass
        if cwd:
            self._state.last_folder_path = str(cwd)
        if url:
            self._state.last_url = str(url)
        if contact:
            self._state.last_contact = str(contact)

    def add_history(self, entry: dict):
        with self._lock:
            self._state.execution_history.append(entry)
            if len(self._state.execution_history) > self._max_history:
                self._state.execution_history = self._state.execution_history[-self._max_history:]

            self._update_context_from_entry(entry)
            self._save_to_disk()

    def remember_fact(self, key: str, value: str):
        with self._lock:
            normalized_key = str(key).strip().lower()
            if not normalized_key:
                return False

            self._state.facts[normalized_key] = str(value).strip()
            self._save_to_disk()
            return True

    def recall_fact(self, key: str):
        with self._lock:
            normalized_key = str(key).strip().lower()
            return self._state.facts.get(normalized_key)

    def forget_fact(self, key: str):
        with self._lock:
            normalized_key = str(key).strip().lower()
            if normalized_key in self._state.facts:
                del self._state.facts[normalized_key]
                self._save_to_disk()
                return True
            return False

    def list_facts(self):
        with self._lock:
            return dict(self._state.facts)

    def reset(self):
        with self._lock:
            self._state = SessionStateSchema()
            self._save_to_disk()
