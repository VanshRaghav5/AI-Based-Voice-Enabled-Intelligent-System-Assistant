from backend.core.execution.assistant_controller import AssistantController
from backend.services.voice_service import listen, speak
from backend.utils.logger import logger
from backend.utils.settings import EXIT_COMMANDS
from backend.core.execution.persona import persona


controller = AssistantController()


def get_confirmation(message: str) -> bool:
    """Ask user for confirmation via voice.
    
    Args:
        message: The confirmation message to speak.
        
    Returns:
        True if user says yes, False if user says no.
    """
    # Speak confirmation in selected persona style
    speak(persona.stylize_response(message, status="confirmation_required"))
    speak(persona.confirmation_instruction())
    
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
            if normalized in [command.lower().strip() for command in EXIT_COMMANDS]:
                speak(persona.shutdown_message())
                logger.info("Assistant terminated by user.")
                break

            # ---- PERSONA SWITCHING ----
            if "switch persona" in normalized or "change persona" in normalized:
                from backend.utils.assistant_config import assistant_config
                
                # Extract persona name from command
                available_personas = ["butler", "professional", "friendly", "concise"]
                new_persona = None
                
                for persona_name in available_personas:
                    if persona_name in normalized:
                        new_persona = persona_name
                        break
                
                if new_persona:
                    # Update config and reload persona
                    if assistant_config.set("assistant.active_persona", new_persona):
                        persona.reload()
                        speak(persona.stylize_response(f"Persona switched to {new_persona}", status="success"))
                        logger.info(f"[App] Switched persona to: {new_persona}")
                    else:
                        speak(persona.stylize_response("Failed to switch persona", status="error"))
                else:
                    # List available personas
                    personas_list = ", ".join(available_personas)
                    speak(persona.stylize_response(f"Available personas are: {personas_list}", status="info"))
                continue

            # ---- PROCESS COMMAND ----
            result = controller.process(text)

            # Debug print (very important while building agents)
            logger.info(f"Controller result: {result}")

            # ---- SAFETY CHECKS ----
            if not isinstance(result, dict):
                speak(persona.stylize_response("Unexpected controller response.", status="error"))
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

            speak(persona.stylize_response(response, status=result.get("status", "info")))

        except KeyboardInterrupt:
            speak(persona.interrupted_message())
            break

        except Exception as e:
            logger.error(f"[App Error] {e}")
            speak(persona.error_message())


if __name__ == "__main__":
    run_forever()
