from backend.core.execution.assistant_controller import AssistantController
from backend.services.voice_service import listen, speak


controller = AssistantController()


def process_once():
    text = listen()
    result = controller.process(text)
    speak(result.get("message", "Done"))


if __name__ == "__main__":
    process_once()
