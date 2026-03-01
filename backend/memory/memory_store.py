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
