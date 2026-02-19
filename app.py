from backend.core.assistant_controller import AssistantController
from backend.voice_engine.audio_pipeline import listen, speak
from backend.config.logger import logger


controller = AssistantController()


def run_forever():
    logger.info("Assistant started. Say 'exit' to quit.")

    while True:
        try:
            text = listen()

            if not text:
                continue

            normalized = text.lower().strip()

            # ---- EXIT CONDITION ----
            if normalized in ["exit", "quit", "shutdown", "stop assistant"]:
                speak("Shutting down. Goodbye.")
                logger.info("Assistant terminated by user.")
                break

            # ---- PROCESS COMMAND ----
            result = controller.process(text)

            # Debug print (very important while building agents)
            logger.info(f"Controller result: {result}")

            # ---- SAFETY CHECKS ----
            if not isinstance(result, dict):
                speak("Unexpected controller response.")
                continue

            response = result.get("message")

            # If message is None OR empty string
            if not response or not response.strip():
                response = "I understood your command, but I have no reply yet."

            speak(response)

        except KeyboardInterrupt:
            speak("Interrupted. Goodbye.")
            break

        except Exception as e:
            logger.error(f"[App Error] {e}")
            speak("An error occurred.")


if __name__ == "__main__":
    run_forever()
