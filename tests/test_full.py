import subprocess
import json

def build_prompt(user_command):
    """Build the full prompt from the template."""
    prompt = f"""You are an intent classification and entity extraction engine.

Choose EXACTLY ONE intent from the ALLOWED INTENTS list.
If none apply, choose "unknown".

ALLOWED INTENTS:
open_application
open_application_and_navigate
play_music
get_weather
get_fact
get_definition
get_tips
unknown

Entity extraction rules:
- For open_application_and_navigate:
  - Extract "application" (e.g., chrome, firefox)
  - Extract "url" as a fully qualified URL (https://...)
- If an entity is not present, omit it.
- Do NOT use arrays for entities.

User command: "{user_command}"

Return ONLY this JSON schema:
{{ "intent": "", "entities": {{}}, "confidence": 0.0 }}

Confidence rules:
- Must be between 0.5 and 0.95
- Never return 1.0"""
    return prompt

def test_ollama_with_prompt(user_command):
    """Test with the full formatted prompt."""
    print(f"\n{'='*70}")
    print(f"User Command: '{user_command}'")
    print('='*70)
    
    full_prompt = build_prompt(user_command)
    
    try:
        result = subprocess.run(
            ["ollama", "run", "intent-engine", full_prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip()
        print("\nRaw Output:")
        print(output)
        
        # Try to parse JSON
        try:
            parsed = json.loads(output)
            print("\n✅ Parsed JSON:")
            print(json.dumps(parsed, indent=2))
            return parsed
        except json.JSONDecodeError:
            print("\n⚠️  Output is not valid JSON - trying to extract JSON...")
            # Try to find JSON in the output
            import re
            json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', output)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    print("✅ Extracted JSON:")
                    print(json.dumps(parsed, indent=2))
                    return parsed
                except:
                    pass
            print("❌ Could not extract valid JSON")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Query timed out")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    test_commands = [
        "Open Chrome and go to YouTube",
        "Play Bohemian Rhapsody by Queen",
        "What's the weather in Tokyo?",
    ]
    
    for cmd in test_commands:
        result = test_ollama_with_prompt(cmd)
        if result:
            # Test with planner
            print("\n[Testing with planner...]")
            try:
                from planner_complete import plan
                planner_result = plan(result)
                print(json.dumps(planner_result, indent=2))
            except Exception as e:
                print(f"Planner error: {e}")
        print("\n")
