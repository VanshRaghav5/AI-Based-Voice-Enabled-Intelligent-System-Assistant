"""Tests for the phase 2 planner architecture."""
from backend.core.intent.classifier import IntentClassifier
from backend.core.planner.planner import Planner
from backend.core.planner.schema import Plan, Step
from backend.core.planner.workflows import (
    organize_files,
    open_app_workflow,
    run_command_workflow,
    search_web_workflow,
    start_work_session,
)


class FakeLLMClient:
    def __init__(self, response, available=True, source="ollama"):
        self._response = response
        self.ollama_available = available
        self.last_source = source
        self.model = "fake-model"
        self.ollama_api_url = "http://localhost:11434"
        self.system_prompt = "You are a planner."

    def generate(self, prompt):
        """Generate response from prompt (new core method)."""
        import json
        # Return JSON string for new generate() method
        if isinstance(self._response, dict):
            return json.dumps(self._response)
        return json.dumps(self._response) if self._response else None

    def generate_plan(self, prompt):
        return self._response


def test_plan_schema_objects():
    step = Step(1, "open_app", {"app_name": "code"})
    plan = Plan("Start work session", [step], True)

    assert plan.goal == "Start work session"
    assert plan.steps[0].action == "open_app"
    assert plan.requires_confirmation is True


def test_start_work_session_workflow():
    steps = start_work_session()

    assert len(steps) == 3
    assert steps[0]["action"] == "open_app"
    assert steps[1]["action"] == "run_command"
    assert steps[2]["action"] == "open_url"


def test_organize_files_workflow():
    steps = organize_files()

    assert len(steps) == 2
    assert steps[0]["action"] == "list_directory"
    assert steps[1]["action"] == "organize_folder"


def test_additional_workflows_exist():
    assert run_command_workflow("echo test")[0]["action"] == "run_command"
    assert open_app_workflow("notepad")[0]["action"] == "open_app"
    assert search_web_workflow("python")[0]["action"] == "search_google"


def test_planner_creates_plan_for_start_work_session():
    classifier = IntentClassifier()
    planner = Planner()

    intent = classifier.classify("Start my ML work")
    plan = planner.create_plan(intent, "Start my ML work")

    assert plan.goal == "Start work session"
    assert [step.action for step in plan.steps] == ["open_app", "run_command", "open_url"]
    assert plan.steps[0].params == {"app_name": "code"}


def test_planner_creates_plan_for_organize_files():
    classifier = IntentClassifier()
    planner = Planner()

    intent = classifier.classify("organize these files")
    plan = planner.create_plan(intent, "organize these files")

    assert plan.goal == "Organize files"
    assert [step.action for step in plan.steps] == ["list_directory", "organize_folder"]


def test_planner_uses_unknown_fallback():
    planner = Planner(llm_client=FakeLLMClient({}))

    plan = planner.create_plan({"intent": "unknown", "confidence": 0.5}, "tell me a joke")

    assert plan.goal == "Unknown task"
    assert plan.steps == []
    assert plan.requires_confirmation is False


def test_planner_uses_llm_for_unknown_intent_when_available():
    planner = Planner(
        llm_client=FakeLLMClient(
            {
                "goal": "Dynamic task plan",
                "steps": [
                    {"action": "open_app", "params": {"app_name": "code"}},
                    {"action": "run_command", "params": {"command": "jupyter notebook"}},
                ],
            },
            available=True,
            source="ollama",
        )
    )

    plan = planner.create_plan({"intent": "unknown", "confidence": 0.5}, "orchestrate a multi-step environment setup")

    assert plan.goal == "LLM-generated task plan"
    assert [step.action for step in plan.steps] == ["open_app", "run_command"]
    assert plan.metadata["planner_mode"] == "llm"
    assert plan.metadata["plan_source"] == "ollama"


def test_planner_reflection_normalizes_llm_output():
    planner = Planner(llm_client=FakeLLMClient({}, available=True))
    plan = Plan("Test plan", [Step(0, "list_memory", {})])

    planner._invoke_llm_json = lambda prompt: {
        "summary": "Retry with a safer plan",
        "success": False,
        "issues": ["First step failed"],
        "memory_updates": [{"key": "last_hint", "value": "use list_memory"}],
        "should_replan": True,
        "next_steps": [{"action": "list_memory", "params": {}}],
    }

    reflection = planner.reflect_on_execution(
        "check my memory",
        plan,
        {"success": False, "error": "boom", "failed_step": 0},
    )

    assert reflection["should_replan"] is True
    assert reflection["next_steps"][0]["action"] == "list_memory"
    assert reflection["memory_updates"][0]["key"] == "last_hint"


def test_planner_continue_work_uses_memory_context():
    planner = Planner()
    context = {
        "session": {"last_plan": "Resume model training"},
        "long_term": {"project_path": "."},
    }

    plan = planner.create_plan({"intent": "continue_work", "confidence": 0.9}, "continue my work", context)

    assert plan.goal == "Continue previous work"
    assert len(plan.steps) >= 1
    assert plan.steps[0].action in {"open_project", "list_memory"}


def test_planner_continue_work_restores_start_session_from_last_intent():
    planner = Planner()
    context = {
        "session": {},
        "long_term": {
            "last_intent": "start_work_session",
            "last_plan": "Start work session",
        },
    }

    plan = planner.create_plan({"intent": "continue_work", "confidence": 0.9}, "continue my work", context)

    assert plan.goal == "Continue previous work"
    assert len(plan.steps) == 3
    assert [step.action for step in plan.steps] == ["open_app", "run_command", "open_url"]


def test_planner_open_project_uses_persistent_project_path():
    planner = Planner()
    context = {
        "session": {},
        "long_term": {"project_path": "D:/ML_Project"},
    }

    plan = planner.create_plan({"intent": "open_project", "confidence": 0.88}, "open my project", context)

    assert plan.goal == "Open project"
    assert len(plan.steps) == 1
    assert plan.steps[0].action == "open_project"
    assert plan.steps[0].params["path"] == "D:/ML_Project"
