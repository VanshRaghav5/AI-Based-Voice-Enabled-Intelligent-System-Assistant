def map_text_to_command(text: str) -> dict:
    """
    Temporary rule-based intent mapper.
    This will later be replaced by AI module.
    """

    text = text.lower()

    # ---------- APP ----------
    if "open chrome" in text:
        return {"intent": "open_app", "target": "chrome"}

    if "open notepad" in text:
        return {"intent": "open_app", "target": "notepad"}

    # ---------- SYSTEM ----------
    if "lock system" in text:
        return {"intent": "lock"}

    # ---------- BROWSER ----------
    if "open youtube" in text:
        return {"intent": "open_youtube"}

    if "search" in text:
        query = text.replace("search", "").strip()
        return {"intent": "search_google", "target": query}

    return {"intent": "unknown"}
