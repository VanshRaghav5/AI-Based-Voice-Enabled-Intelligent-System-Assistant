import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


from backend.memory.command_processor import MemoryCommandProcessor
from backend.memory.session_state import SessionState


class FakeMemoryStore:
    def __init__(self):
        self._facts = {}

    def remember_fact(self, key, value):
        self._facts[str(key).strip().lower()] = str(value).strip()
        return True

    def recall_fact(self, key):
        return self._facts.get(str(key).strip().lower())

    def forget_fact(self, key):
        normalized = str(key).strip().lower()
        return self._facts.pop(normalized, None) is not None

    def list_facts(self):
        return dict(self._facts)


def test_session_state_get_state_returns_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.memory.session_state.assistant_config.get", lambda key, default=None: {
        "memory.enabled": True,
        "memory.max_history": 200,
        "memory.file": str(tmp_path / "session.json"),
    }.get(key, default))

    session = SessionState()
    snapshot = session.get_state()
    snapshot.facts["color"] = "blue"

    fresh_snapshot = session.get_state()

    assert "color" not in fresh_snapshot.facts


def test_memory_command_processor_handles_round_trip_memory_commands():
    processor = MemoryCommandProcessor(FakeMemoryStore())

    remember_result = processor.process("remember favorite color is blue")
    recall_result = processor.process("recall favorite color")
    forget_result = processor.process("forget favorite color")
    missing_result = processor.process("recall favorite color")

    assert remember_result["status"] == "success"
    assert recall_result["status"] == "success"
    assert "blue" in recall_result["message"].lower()
    assert forget_result["status"] == "success"
    assert missing_result["status"] == "error"