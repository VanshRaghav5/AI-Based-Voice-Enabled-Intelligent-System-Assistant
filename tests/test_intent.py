#!/usr/bin/env python3
"""
Test script for the Ollama Intent Engine
"""
import json
import subprocess
from planner_complete import plan

def query_ollama(prompt):
    """Send a query to the Ollama intent-engine model."""
    try:
        result = subprocess.run(
            ["ollama", "run", "intent-engine", prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Error running Ollama: {result.stderr}")
            return None
        
        # Parse the JSON output
        output = result.stdout.strip()
        return json.loads(output)
    
    except subprocess.TimeoutExpired:
        print("Ollama query timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw output: {output}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def test_intent(user_command):
    """Test a single user command through the full pipeline."""
    print(f"\n{'='*70}")
    print(f"User Command: {user_command}")
    print('='*70)
    
    # Step 1: Get LLM output
    print("\n[Step 1] Querying Ollama model...")
    llm_output = query_ollama(user_command)
    
    if not llm_output:
        print("❌ Failed to get response from Ollama")
        return
    
    print(f"\n[LLM Output]")
    print(json.dumps(llm_output, indent=2))
    
    # Step 2: Run through planner
    print(f"\n[Step 2] Processing through planner...")
    try:
        result = plan(llm_output)
        print(f"\n[Planner Result]")
        print(json.dumps(result, indent=2))
        
        if result.get("status") == "success":
            print(f"\n✅ SUCCESS: {result.get('message')}")
        else:
            print(f"\n⚠️  {result.get('message')}")
    
    except Exception as e:
        print(f"\n❌ Planner Error: {e}")


def main():
    """Run multiple test cases."""
    test_cases = [
        "Open Chrome and go to YouTube",
        "Play Bohemian Rhapsody by Queen",
        "What's the weather in Tokyo?",
        "Open Spotify",
        "Tell me a fun fact about Mars",
        "Define machine learning",
        "Give me tips on public speaking",
        "I'm not sure what I want"
    ]
    
    print("="*70)
    print("OLLAMA INTENT ENGINE - TEST SUITE")
    print("="*70)
    
    for command in test_cases:
        test_intent(command)
    
    print(f"\n{'='*70}")
    print("Test suite completed!")
    print('='*70)


if __name__ == "__main__":
    main()
