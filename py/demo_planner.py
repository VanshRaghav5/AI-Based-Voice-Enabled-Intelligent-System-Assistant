"""Demonstration of the phase 2 planner with full logging."""
from backend.core.intent.classifier import IntentClassifier
from backend.core.memory.memory_manager import MemoryManager
from backend.core.planner.planner import Planner


def demo():
    print("\n" + "=" * 80)
    print("PHASE 2 PLANNER DEMO - Intent Classifier → Planner → Execution Plan")
    print("=" * 80 + "\n")

    classifier = IntentClassifier()
    planner = Planner()
    memory = MemoryManager()

    # Test cases
    test_inputs = [
        "Start my ML work",
        "organize these files please",
        "run python script.py",
    ]

    for user_input in test_inputs:
        print(f"\n{'=' * 80}")
        print(f"USER INPUT: {user_input!r}")
        print(f"{'=' * 80}")

        # Step 1: Classify intent
        intent_data = classifier.classify(user_input)
        
        # Step 2: Create plan
        plan = planner.create_plan(intent_data, user_input, memory.get_context())

        # Step 3: Display results
        print(f"\n📋 PLAN RESULT:")
        print(f"   Goal: {plan.goal}")
        print(f"   Requires Confirmation: {plan.requires_confirmation}")
        print(f"   Total Steps: {len(plan.steps)}\n")

        if plan.steps:
            print(f"   Steps:")
            for step in plan.steps:
                print(f"      {step.step_id}: {step.action}")
                if step.params:
                    for key, value in step.params.items():
                        print(f"         - {key}: {value}")


if __name__ == "__main__":
    demo()
