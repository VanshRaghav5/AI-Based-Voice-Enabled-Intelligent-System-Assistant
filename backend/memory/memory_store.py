import threading
from backend.memory.session_state import SessionState


class MemoryStore:

    def __init__(self):
        self._lock = threading.Lock()
        self._session = SessionState()

    def get_state(self):
        with self._lock:
            return self._session.get_state()

    def update(self, updates: dict):
        with self._lock:
            self._session.update(updates)

    def add_history(self, entry: dict):
        with self._lock:
            self._session.add_history(entry)

    def reset(self):
        with self._lock:
            self._session.reset()

    def remember_fact(self, key: str, value: str):
        with self._lock:
            return self._session.remember_fact(key, value)

    def recall_fact(self, key: str):
        with self._lock:
            return self._session.recall_fact(key)

    def forget_fact(self, key: str):
        with self._lock:
            return self._session.forget_fact(key)

    def list_facts(self):
        with self._lock:
            return self._session.list_facts()
