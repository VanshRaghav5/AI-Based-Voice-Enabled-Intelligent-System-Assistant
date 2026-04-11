"""Phase 4 memory demo: resume work after assistant restart."""
from __future__ import annotations

from pathlib import Path

from backend.core.execution.engine import ExecutionEngine
from backend.core.execution.tool_registry import ToolRegistry
from backend.core.intent.classifier import IntentClassifier
from backend.core.memory.memory_manager import MemoryManager
from backend.core.planner.planner import Planner
from backend.tools.dev_tools import register_all_tools


def _build_runtime(memory_file: Path):
    registry = ToolRegistry()
    register_all_tools(registry)
    memory = MemoryManager(long_term_file_path=str(memory_file))
    planner = Planner()
    classifier = IntentClassifier()
    engine = ExecutionEngine(registry, max_retries=1, memory=memory)
    return classifier, planner, engine, memory


def run_demo() -> None:
    project_root = Path(__file__).resolve().parents[1]
    memory_file = project_root / "backend" / "data" / "phase4_demo_memory.json"

    print("=" * 90)
    print("PHASE 4 DEMO: Start work -> Close system -> Continue work")
    print("=" * 90)

    print("\n[1] User says: Start my ML work")
    classifier, planner, engine, memory = _build_runtime(memory_file)
    start_input = "Start my ML work"
    start_intent = classifier.classify(start_input)
    start_plan = planner.create_plan(start_intent, start_input, memory.get_context())
    start_result = engine.execute_plan(start_plan)

    print(f"Intent: {start_intent['intent']}")
    print(f"Plan steps: {[step.action for step in start_plan.steps]}")
    print(f"Execution success: {start_result.get('success')}")
    print(f"Persisted memory: {memory.get_context().get('long_term', {})}")

    print("\n[2] Close system (simulated as process restart)")
    del classifier, planner, engine, memory

    print("\n[3] User says: Continue my work")
    classifier, planner, engine, memory = _build_runtime(memory_file)
    continue_input = "Continue my work"
    continue_intent = classifier.classify(continue_input)
    continue_plan = planner.create_plan(continue_intent, continue_input, memory.get_context())
    continue_result = engine.execute_plan(continue_plan)

    print(f"Intent: {continue_intent['intent']}")
    print(f"Restored steps: {[step.action for step in continue_plan.steps]}")
    print(f"Execution success: {continue_result.get('success')}")

    print("\nResult: resume happened automatically from long-term memory.")
    print("=" * 90)


if __name__ == "__main__":
    run_demo()
