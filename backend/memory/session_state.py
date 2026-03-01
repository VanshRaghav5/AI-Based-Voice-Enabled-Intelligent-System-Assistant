from backend.memory.state_schema import SessionStateSchema


class SessionState:

    def __init__(self):
        self._state = SessionStateSchema()

    def get_state(self):
        return self._state

    def update(self, updates: dict):
        for key, value in updates.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)

    def add_history(self, entry: dict):
        self._state.execution_history.append(entry)

    def reset(self):
        self._state = SessionStateSchema()
