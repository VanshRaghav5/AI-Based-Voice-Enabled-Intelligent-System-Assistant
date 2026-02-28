import subprocess
import json
import sys

def test_ollama(prompt):
    """Test a single query with the Ollama model."""
    print(f"\nUser Command: '{prompt}'")
    print("-" * 70)
    
    try:
        # Run ollama command
        result = subprocess.run(
            ["ollama", "run", "intent-engine", prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("\nRaw Output:")
        print(result.stdout)
        
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
        
        # Try to parse as JSON
        try:
            output = result.stdout.strip()
            parsed = json.loads(output)
            print("\nParsed JSON:")
            print(json.dumps(parsed, indent=2))
            return parsed
        except json.JSONDecodeError:
            print("\n⚠️  Output is not valid JSON")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Query timed out after 30 seconds")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    # Test a simple command
    test_ollama("Open Chrome and go to YouTube")
