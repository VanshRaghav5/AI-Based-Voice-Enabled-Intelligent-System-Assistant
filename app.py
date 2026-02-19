from backend.core.assistant_controller import AssistantController
from backend.voice_engine.audio_pipeline import listen, speak
from backend.config.logger import logger


controller = AssistantController()


def get_confirmation(message: str) -> bool:
    """Ask user for confirmation via voice.
    
    Args:
        message: The confirmation message to speak.
        
    Returns:
        True if user says yes, False if user says no.
    """
    # Speak the confirmation message
    speak(message)
    speak("Say yes to confirm or no to cancel.")
    
    # Listen for confirmation
    try:
        response = listen()
        if response:
            response_lower = response.lower().strip()
            if any(x in response_lower for x in ["yes", "confirm", "approve", "go ahead", "proceed", "ok", "okay"]):
                logger.info("[App] User confirmed action")
                return True
            else:
                logger.info("[App] User cancelled action")
                return False
    except Exception as e:
        logger.error(f"[App] Error getting confirmation: {e}")
        speak("I couldn't hear your response. Cancelling action.")
        return False
    
    return False


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

            # ---- HANDLE CONFIRMATION REQUIRED ----
            if result.get("status") == "confirmation_required":
                confirm_msg = result.get("message", "Confirm this action?")
                approved = get_confirmation(confirm_msg)
                
                # Execute confirmed or denied action
                final_result = controller.confirm_action(approved)
                response = final_result.get("message")
                logger.info(f"Confirmation result: {final_result}")
            else:
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
