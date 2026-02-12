from voice_engine.audio_pipeline import listen, speak
from shared_interfaces.simple_intent_mapper import map_text_to_command
from automation.automation_router import execute


print("🎙 Assistant Started...")
print("Say 'exit assistant' to stop.")

while True:

    text = listen()
    print("User said:", text)

    if not text:
        speak("I did not hear anything.")
        continue

    if "exit assistant" in text.lower():
        speak("Goodbye.")
        break

    command = map_text_to_command(text)
    print("Mapped command:", command)

    if command["intent"] == "unknown":
        speak("Sorry, I don't understand that yet.")
        continue

    result = execute(command)
    print("Automation result:", result)

    speak(result["message"])
