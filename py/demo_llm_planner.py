"""
DEMO: LLM as the core reasoning engine
========================================

This demonstrates how LLM now drives intelligent planning,
not just scaffolding.

Run this to see LLM thinking in real-time.
"""
import json
import os
from backend.services.llm_service import LLMClient
from backend.core.planner.planner import Planner


def demo_llm_reasoning():
    """Show LLM thinking and planning in real-time."""
    
    print("\n" + "="*70)
    print("DEMO: LLM-BASED INTELLIGENT PLANNING")
    print("="*70 + "\n")
    
    # Initialize
    llm_client = LLMClient()
    planner = Planner(llm_client=llm_client)
    
    # Test cases: unknown tasks that need LLM reasoning
    test_tasks = [
        "Setup my ML project with TensorFlow and Jupyter",
        "Prepare a backup of all my Python files",
        "Create a new React web app boilerplate",
        "Organize my downloads folder by file type",
    ]
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n📝 TASK {i}: {task}")
        print("-" * 70)
        
        # Create plan (will use LLM for unknowns)
        intent_data = {"intent": "unknown", "confidence": 0.0}
        plan = planner.create_plan(intent_data, task)
        
        if plan:
            print(f"\n✅ GOAL: {plan.goal}")
            print(f"   Source: {plan.metadata.get('planner_mode', 'unknown')}")
            print(f"\n📋 PLAN ({len(plan.steps)} steps):")
            
            for step in plan.steps:
                params_str = json.dumps(step.params, indent=12) if step.params else "{}"
                print(f"\n   Step {step.step_id + 1}: {step.action}")
                print(f"   Params: {params_str}")
        else:
            print("❌ Failed to create plan")
        
        print()


def demo_hybrid_approach():
    """Show the hybrid rule-based + LLM approach."""
    
    print("\n" + "="*70)
    print("DEMO: HYBRID APPROACH (Rule-based + LLM)")
    print("="*70 + "\n")
    
    llm_client = LLMClient()
    planner = Planner(llm_client=llm_client)
    
    test_cases = [
        ("Known: Start work", {"intent": "start_work_session", "confidence": 0.95}, "Start my day"),
        ("Unknown: Complex task", {"intent": "unknown", "confidence": 0.0}, "Build a CI/CD pipeline for my project"),
    ]
    
    for label, intent_data, task in test_cases:
        print(f"\n🧠 {label}")
        print("-" * 70)
        
        plan = planner.create_plan(intent_data, task)
        
        if plan:
            planner_mode = plan.metadata.get("planner_mode", "unknown")
            emoji = "⚡" if planner_mode == "rule_based" else "🤖"
            
            print(f"{emoji} Mode: {planner_mode}")
            print(f"   Goal: {plan.goal}")
            print(f"   Steps: {len(plan.steps)}")
            print(f"   First step: {plan.steps[0].action if plan.steps else 'N/A'}")
        
        print()


def demo_llm_generates_response():
    """Show LLM generating raw responses (before parsing)."""
    
    print("\n" + "="*70)
    print("DEMO: LLM Response Generation")
    print("="*70 + "\n")
    
    llm_client = LLMClient()
    
    if not llm_client.ollama_available:
        print("⚠️  Ollama not available - skipping live response demo")
        print("   (Make sure Ollama is running on localhost:11434)")
        return
    
    # Build a planning prompt
    prompt = """You are an AI planner.

User request: Setup Python development environment

Available tools:
- open_app
- run_command
- create_file

Break into steps. Return JSON array:
[{"action": "...", "params": {...}}]"""
    
    print("PROMPT:")
    print(prompt)
    print("\n" + "-"*70)
    print("\nLLM RESPONSE:")
    
    # Call LLM's generate() method directly
    response = llm_client.generate(prompt)
    
    if response:
        print(response[:500])  # Show first 500 chars
        print("..." if len(response) > 500 else "")
    else:
        print("⚠️  No response from LLM")
    
    print()


if __name__ == "__main__":
    print("\n🚀 Starting LLM Reasoning Demos\n")
    
    # Show hybrid approach first (faster)
    demo_hybrid_approach()
    
    # Show generic reasoning 
    demo_llm_generates_response()
    
    # Show full LLM planning (if Ollama is available)
    try:
        llm_client = LLMClient()
        if llm_client.ollama_available:
            print("\n" + "="*70)
            print("Running full LLM planning demo...")
            print("(This may take a moment as LLM is thinking)")
            print("="*70)
            demo_llm_reasoning()
        else:
            print("\n⚠️  Ollama not available - skipping full LLM demo")
            print("   To run: Start Ollama on localhost:11434")
    except Exception as e:
        print(f"\n⚠️  Error in LLM demo: {e}")
    
    print("\n✅ Demo complete!")
    print("\n📌 KEY INSIGHT:")
    print("   - LLM is now the CORE reasoning engine")
    print("   - Rule-based = fast path for known tasks")
    print("   - LLM = flexible path for unknown tasks")
    print("   - System thinks before acting ✨")
