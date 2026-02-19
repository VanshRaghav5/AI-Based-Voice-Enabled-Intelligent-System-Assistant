from backend.core.assistant_controller import AssistantController
from backend.voice_engine.audio_pipeline import listen, speak


controller = AssistantController()


def process_once():
    text = listen()
    result = controller.process(text)
    speak(result.get("message", "Done"))


if __name__ == "__main__":
    process_once()
