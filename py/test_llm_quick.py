"""Quick test of LLM planner."""
from backend.services.llm_service import LLMClient  
from backend.core.planner.planner import Planner
import time

print("Testing LLM Planner Integration...\n")

llm_client = LLMClient()
planner = Planner(llm_client=llm_client)

# Test 1: Known task (rule-based path)
print("TEST 1: Known Task (Rule-based)")
plan = planner.create_plan({'intent': 'start_work_session', 'confidence': 0.95}, 'Start my work')
print(f'  Goal: {plan.goal}')
print(f'  Mode: {plan.metadata.get("planner_mode")}')
print(f'  Steps: {len(plan.steps)}')
print()

# Test 2: Unknown task (LLM path)
print("TEST 2: Unknown Task (LLM reasoning)")
start = time.time()
plan = planner.create_plan({'intent': 'unknown', 'confidence': 0.0}, 'Setup Python development environment')
elapsed = time.time() - start

print(f'  Goal: {plan.goal}')
print(f'  Mode: {plan.metadata.get("planner_mode")}')
print(f'  Steps: {len(plan.steps)}')
print(f'  Time: {elapsed:.1f}s')

if plan.steps:
    print(f'\n  First 3 steps:')
    for i, step in enumerate(plan.steps[:3], 1):
        print(f'    {i}. {step.action}: {step.params}')

print("\n✅ LLM Planner Integration Test Complete!")
