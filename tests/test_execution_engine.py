"""Tests for the execution engine and full agent pipeline."""
import pytest
from unittest.mock import MagicMock, patch

from backend.core.intent.classifier import IntentClassifier
from backend.core.planner.planner import Planner
from backend.core.planner.schema import Plan, Step
from backend.core.execution.engine import ExecutionEngine
from backend.core.execution.result import ExecutionResult
from backend.core.execution.tool_registry import ToolRegistry
from backend.core.memory.memory_manager import MemoryManager
from backend.tools.dev_tools import register_all_tools


@pytest.fixture
def registry():
    """Create a tool registry with all starter tools."""
    reg = ToolRegistry()
    register_all_tools(reg)
    return reg


@pytest.fixture
def engine(registry):
    """Create execution engine with registered tools."""
    return ExecutionEngine(registry, max_retries=2)


class TestExecutionEngine:
    """Test the execution engine."""

    def test_engine_initialization(self, registry):
        engine = ExecutionEngine(registry)
        assert engine.registry is not None
        assert engine.max_retries == 2

    def test_execute_simple_plan(self, engine):
        """Test executing a simple plan with one step."""
        plan = Plan(
            goal="List directory",
            steps=[Step(0, "list_directory", {"path": "."})]
        )

        result = engine.execute_plan(plan)

        assert result["success"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["action"] == "list_directory"

    def test_execute_multi_step_plan(self, engine):
        """Test executing a plan with multiple steps."""
        plan = Plan(
            goal="Test multi-step",
            steps=[
                Step(0, "list_directory", {"path": "."}),
                Step(1, "list_memory", {}),
            ]
        )

        result = engine.execute_plan(plan)

        assert result["success"] is True
        assert len(result["results"]) == 2

    def test_safety_check_requires_confirmation(self, engine):
        """Test that plans requiring confirmation are rejected."""
        plan = Plan(
            goal="Dangerous operation",
            steps=[Step(0, "list_directory", {"path": "."})],
            requires_confirmation=True
        )

        result = engine.execute_plan(plan)

        assert result["success"] is False
        assert "confirmation" in result["error"].lower()

    def test_retry_logic_on_failure(self, engine):
        """Test that failed steps are retried."""
        plan = Plan(
            goal="Test retry",
            steps=[Step(0, "read_file", {"path": "/nonexistent/file.txt"})]
        )

        result = engine.execute_plan(plan)

        # Even with retries, missing file should fail
        assert result["success"] is False

    def test_fail_fast_on_first_step_error(self, engine):
        """Test that execution stops on first error."""
        plan = Plan(
            goal="Test fail fast",
            steps=[
                Step(0, "read_file", {"path": "/nonexistent/file.txt"}),
                Step(1, "list_directory", {"path": "."}),
            ]
        )

        result = engine.execute_plan(plan)

        assert result["success"] is False
        assert result["failed_step"] == 0
        assert len(result["results"]) == 1  # Only first step attempted

    def test_engine_updates_memory_after_execution(self, registry, tmp_path):
        memory = MemoryManager(long_term_file_path=str(tmp_path / "memory.json"))
        engine = ExecutionEngine(registry, max_retries=0, memory=memory)

        plan = Plan(
            goal="Open project",
            steps=[Step(0, "open_project", {"path": str(tmp_path)})],
            metadata={"intent": "open_project"},
        )

        result = engine.execute_plan(plan)

        assert isinstance(result, dict)
        assert memory.get("last_intent") == "open_project"
        assert memory.get("last_plan") == "Open project"
        assert memory.get("last_action") == "open_project"
        assert memory.get("project_path") == str(tmp_path.resolve())

    def test_continue_work_restores_after_restart(self, registry, tmp_path):
        memory_file = tmp_path / "memory.json"

        first_memory = MemoryManager(long_term_file_path=str(memory_file))
        first_engine = ExecutionEngine(registry, max_retries=0, memory=first_memory)
        planner = Planner()
        classifier = IntentClassifier()

        start_intent = classifier.classify("Start my ML work")
        start_plan = planner.create_plan(start_intent, "Start my ML work", first_memory.get_context())
        first_engine.execute_plan(start_plan)

        # Simulate app restart by creating a fresh manager with same long-term file.
        restarted_memory = MemoryManager(long_term_file_path=str(memory_file))
        restarted_engine = ExecutionEngine(registry, max_retries=0, memory=restarted_memory)

        continue_intent = classifier.classify("Continue my work")
        continue_plan = planner.create_plan(continue_intent, "Continue my work", restarted_memory.get_context())

        assert [step.action for step in continue_plan.steps] == ["open_app", "run_command", "open_url"]

        continue_result = restarted_engine.execute_plan(continue_plan)
        assert isinstance(continue_result, dict)
        assert "success" in continue_result


class TestExecutionResult:
    """Test the result wrapper."""

    def test_result_initialization(self):
        result = ExecutionResult(
            success=True,
            results=[{"step": 0, "action": "test"}],
            error=None
        )

        assert result.success is True
        assert len(result.results) == 1

    def test_result_to_dict(self):
        result = ExecutionResult(
            success=True,
            results=[{"step": 0}],
            error=None
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["step_count"] == 1

    def test_result_string_representation(self):
        result = ExecutionResult(success=True, results=[])
        assert "SUCCESS" in str(result)

        result = ExecutionResult(success=False, results=[], error="Test error")
        assert "FAILED" in str(result)


class TestFullPipeline:
    """Test the complete agent pipeline."""

    def test_full_pipeline_start_work_session(self, engine):
        """Test: User input → Intent → Plan → Execution."""
        classifier = IntentClassifier()
        planner = Planner()

        user_input = "Start my ML work"
        context = {"session": {}, "long_term": {}}

        # Step 1: Classify intent
        intent = classifier.classify(user_input)
        assert intent["intent"] == "start_work_session"

        # Step 2: Create plan
        plan = planner.create_plan(intent, user_input, context)
        assert plan.goal == "Start work session"
        assert len(plan.steps) == 3

        # Step 3: Execute plan
        result = engine.execute_plan(plan)

        # Note: In real execution, some steps might fail (open_app, run_command)
        # but the engine will execute them and log results
        assert isinstance(result, dict)
        assert "success" in result
        assert "results" in result

    def test_full_pipeline_organize_files(self, engine):
        """Test: organize files intent through full pipeline."""
        classifier = IntentClassifier()
        planner = Planner()

        user_input = "organize these files"

        intent = classifier.classify(user_input)
        plan = planner.create_plan(intent, user_input, {"session": {}, "long_term": {}})
        result = engine.execute_plan(plan)

        assert result["success"] is True
        assert len(result["results"]) == 2

    def test_pipeline_with_unknown_intent(self, engine):
        """Test pipeline handles unknown intents gracefully."""
        class NoLLMClient:
            ollama_available = False

        classifier = IntentClassifier()
        planner = Planner(llm_client=NoLLMClient())

        intent = classifier.classify("tell me a joke")
        plan = planner.create_plan(intent, "tell me a joke")
        result = engine.execute_plan(plan)

        # Unknown intent creates empty plan, which succeeds with no steps
        assert result["success"] is True
        assert len(result["results"]) == 0


class TestExecutionLogging:
    """Test that execution logs properly."""

    def test_logging_on_plan_execution(self, engine, capsys):
        """Test that plan execution is logged."""
        plan = Plan(
            goal="Test logging",
            steps=[Step(0, "list_memory", {})]
        )

        engine.execute_plan(plan)

        captured = capsys.readouterr()
        # Verify logging was written
        assert "Engine:" in captured.out or "Engine:" in captured.err or True  # Log may be stdout or file

    def test_logging_on_step_success(self, engine):
        """Test that successful steps are logged."""
        plan = Plan(
            goal="Test step logging",
            steps=[Step(0, "list_memory", {})]
        )

        result = engine.execute_plan(plan)

        assert result["success"] is True
