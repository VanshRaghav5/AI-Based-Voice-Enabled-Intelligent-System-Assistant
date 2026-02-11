def detect_intent(text: str) -> str:
    text = text.lower()

    if any(word in text for word in ["hello", "hi", "hey"]):
        return "greeting"

    if "time" in text:
        return "time_query"

    if "open notepad" in text:
        return "open_notepad"

    if any(word in text for word in ["bye", "goodbye"]):
        return "farewell"

    return "unknown"

import datetime
import os


def handle_intent(intent: str, text: str) -> str:
    if intent == "greeting":
        return "Hello Vansh. How can I assist you today?"

    if intent == "time_query":
        current_time = datetime.datetime.now().strftime("%H:%M")
        return f"The current time is {current_time}"

    if intent == "open_notepad":
        os.system("start notepad")
        return "Opening Notepad for you."

    if intent == "farewell":
        return "Goodbye. Have a productive day."

    return "I'm not sure how to help with that yet."
