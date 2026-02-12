from voice_engine.audio_pipeline import listen, speak

text = listen()
print("User said:", text)

if text:
    response = "You said " + text
    speak(response)
else:
    speak("I did not hear anything clearly.")
