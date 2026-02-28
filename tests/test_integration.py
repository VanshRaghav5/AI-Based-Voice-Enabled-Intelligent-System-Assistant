import subprocess
import json
import re

def extract_json_from_output(text):
    """Extract JSON object from text that may contain other content."""
    # Try to find JSON pattern
    patterns = [
        r'\{[^{}]*"intent"[^{}]*"entities"[^{}]*"confidence"[^{}]*\}',  # Single line
        r'\{\s*"intent":\s*"[^"]*",\s*"entities":\s*\{[^}]*\},\s*"confidence":\s*[\d.]+\s*\}',  # Multi-line
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                if "intent" in parsed and "entities" in parsed and "confidence" in parsed:
                    return parsed
            except:
                continue
    
    # Try finding it in code blocks
    code_blocks = re.findall(r'```(?:json)?\s*(\{[^`]+\})\s*```', text, re.DOTALL)
    for block in code_blocks:
        try:
            parsed = json.loads(block)
            if "intent" in parsed and "entities" in parsed and "confidence" in parsed:
                return parsed
        except:
            continue
    
    return None

def test_ollama(user_command):
    """Test with ollama and extract JSON."""
    print(f"\n{'='*70}")
    print(f"Testing: '{user_command}'")
    print('='*70)
    
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

    try:
        result = subprocess.run(
            ["ollama", "run", "intent-engine", prompt],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='ignore'
        )
        
        output = result.stdout.strip()
        
        # Extract JSON
        parsed = extract_json_from_output(output)
        
        if parsed:
            print("\n✅ Extracted JSON:")
            print(json.dumps(parsed, indent=2))
            
            # Test with planner
            print("\n[Running through planner...]")
            try:
                from planner_complete import plan
                planner_result = plan(parsed)
                print("\nPlanner Result:")
                print(json.dumps(planner_result, indent=2))
                
                if planner_result.get("status") == "success":
                    print(f"\n✅ {planner_result.get('message')}")
                else:
                    print(f"\n⚠️  {planner_result.get('message')}")
            except Exception as e:
                print(f"❌ Planner error: {e}")
            
            return parsed
        else:
            print("\n❌ Could not extract JSON from output")
            print("\nRaw output (first 500 chars):")
            print(output[:500])
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("="*70)
    print("OLLAMA INTENT ENGINE - INTEGRATION TEST")
    print("="*70)
    
    test_commands = [
        "Open Chrome and go to YouTube",
        "Play Bohemian Rhapsody by Queen",
        "What's the weather in Tokyo?",
        "Open Spotify",
    ]
    
    for cmd in test_commands:
        test_ollama(cmd)
    
    print("\n" + "="*70)
    print("Test complete!")
    print("="*70)
