import json

# Simulated LLM output for testing (in case Ollama is slow)
test_outputs = [
    {
        "intent": "open_application_and_navigate",
        "entities": {
            "application": "chrome",
            "url": "https://www.youtube.com"
        },
        "confidence": 0.92
    },
    {
        "intent": "play_music",
        "entities": {
            "song": "Bohemian Rhapsody",
            "artist": "Queen"
        },
        "confidence": 0.88
    },
    {
        "intent": "get_weather",
        "entities": {
            "location": "Tokyo"
        },
        "confidence": 0.95
    },
    {
        "intent": "open_application",
        "entities": {
            "application": "spotify"
        },
        "confidence": 0.90
    },
    {
        "intent": "unknown",
        "entities": {},
        "confidence": 0.45
    }
]

# Import the planner
from planner_complete import plan

print("="*70)
print("TESTING PLANNER WITH SIMULATED LLM OUTPUTS")
print("="*70)

for i, llm_output in enumerate(test_outputs, 1):
    print(f"\n\n[Test Case {i}]")
    print("-"*70)
    print("LLM Output:")
    print(json.dumps(llm_output, indent=2))
    
    print("\nPlanner Result:")
    try:
        result = plan(llm_output)
        print(json.dumps(result, indent=2))
        
        if result.get("status") == "success":
            print(f"\n✅ {result.get('message')}")
        else:
            print(f"\n⚠️  {result.get('message')}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

print("\n" + "="*70)
print("Testing complete!")
print("="*70)
