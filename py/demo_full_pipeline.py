"""Complete Agent Pipeline Demo: User Input → Intent → Plan → Execution → Result"""
from backend.core.intent.classifier import IntentClassifier
from backend.core.planner.planner import Planner
from backend.core.execution.engine import ExecutionEngine
from backend.core.execution.tool_registry import ToolRegistry
from backend.core.memory.memory_manager import MemoryManager
from backend.tools.dev_tools import register_all_tools


def demo_full_agent_pipeline():
    """Demonstrate the complete agent pipeline with full logging."""
    print("\n" + "=" * 100)
    print("AGENT PIPELINE DEMO: User Input → Intent → Planner → Execution Engine → Tools → Result")
    print("=" * 100 + "\n")

    # Initialize components
    classifier = IntentClassifier()
    planner = Planner()
    memory = MemoryManager()
    registry = ToolRegistry()
    register_all_tools(registry)
    engine = ExecutionEngine(registry, max_retries=2, memory=memory)

    # Test cases
    test_cases = [
        ("Start my ML work", "start_work_session"),
        ("organize these files please", "organize_files"),
        ("search for python tutorials", "search_web"),
    ]

    for user_input, expected_intent in test_cases:
        print(f"\n{'=' * 100}")
        print(f"USER INPUT: {user_input!r}")
        print(f"{'=' * 100}\n")

        print(f"[1] INTENT CLASSIFICATION")
        print("-" * 100)
        intent_data = classifier.classify(user_input)
        print(f"  Intent: {intent_data['intent']}")
        print(f"  Confidence: {intent_data['confidence']}")
        print(f"  Keywords: {intent_data['matched_keywords']}\n")

        print(f"[2] PLAN GENERATION")
        print("-" * 100)
        plan = planner.create_plan(intent_data, user_input, memory.get_context())
        print(f"  Goal: {plan.goal}")
        print(f"  Requires Confirmation: {plan.requires_confirmation}")
        print(f"  Total Steps: {len(plan.steps)}")
        if plan.steps:
            print(f"  Steps:")
            for step in plan.steps:
                print(f"    - {step.step_id}: {step.action}")
                for key, value in step.params.items():
                    print(f"        {key}: {value}")
        print()

        print(f"[3] PLAN EXECUTION")
        print("-" * 100)
        result = engine.execute_plan(plan)
        print(f"  Status: {'SUCCESS' if result['success'] else 'FAILED'}")
        print(f"  Steps Executed: {len(result['results'])}")
        if not result["success"]:
            print(f"  Error: {result.get('error', 'Unknown')}")
            if result.get('failed_step') is not None:
                print(f"  Failed Step: {result['failed_step']}")
        print()

        print(f"[4] EXECUTION DETAILS")
        print("-" * 100)
        for step_result in result["results"]:
            status = "✓" if step_result["result"].get("success") else "✗"
            print(f"  {status} Step {step_result['step']}: {step_result['action']}")
            if step_result["result"].get("message"):
                print(f"      Message: {step_result['result']['message']}")
        print()

        print(f"[5] MEMORY SNAPSHOT")
        print("-" * 100)
        print(f"  Session: {memory.get_context().get('session', {})}")
        print(f"  Long-term: {memory.get_context().get('long_term', {})}\n")


if __name__ == "__main__":
    demo_full_agent_pipeline()
    print("\n" + "=" * 100)
    print("PIPELINE COMPLETE")
    print("=" * 100 + "\n")
