"""Phase 4 tests: session/long-term memory and unified manager."""
from __future__ import annotations

from backend.core.memory.long_term_memory import LongTermMemory
from backend.core.memory.memory_manager import MemoryManager
from backend.core.memory.session_memory import SessionMemory


def test_session_memory_set_get_all():
    memory = SessionMemory()

    memory.set("last_intent", "start_work_session")
    memory.set("last_plan", "Start work session")
    memory.set("last_action", "open_app")

    assert memory.get("last_intent") == "start_work_session"
    assert memory.get("last_plan") == "Start work session"
    assert memory.get("last_action") == "open_app"
    assert memory.get_all()["last_intent"] == "start_work_session"


def test_long_term_memory_persists_data(tmp_path):
    memory_file = tmp_path / "memory.json"
    memory = LongTermMemory(str(memory_file))

    memory.set("project_path", "D:/ML_Project")

    reloaded = LongTermMemory(str(memory_file))
    assert reloaded.get("project_path") == "D:/ML_Project"


def test_memory_manager_context_and_fallback(tmp_path):
    memory_file = tmp_path / "memory.json"
    memory = MemoryManager(long_term_file_path=str(memory_file))

    memory.set("last_intent", "continue_work")
    memory.set("project_path", "D:/ML_Project", persistent=True)

    assert memory.get("last_intent") == "continue_work"
    assert memory.get("project_path") == "D:/ML_Project"

    context = memory.get_context()
    assert context["session"]["last_intent"] == "continue_work"
    assert context["long_term"]["project_path"] == "D:/ML_Project"
