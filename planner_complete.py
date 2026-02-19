CONFIDENCE_THRESHOLD = 0.7

def plan(llm_output):
    intent = llm_output["intent"]
    entities = llm_output["entities"]
    confidence = llm_output["confidence"]

    if confidence < CONFIDENCE_THRESHOLD:
        return ask_for_clarification()

    if intent == "unknown":
        return ask_for_clarification()

    validate_entities(intent, entities)

    if intent == "open_application":
        return open_application(entities["application"])

    if intent == "open_application_and_navigate":
        return open_application_and_navigate(
            entities["application"],
            entities["url"]
        )

    if intent == "play_music":
        return play_music(
            song=entities["song"],
            artist=entities.get("artist")
        )

    if intent == "get_weather":
        return get_weather(entities["location"])

    if intent == "get_fact":
        return get_fact(
            entities["subject"],
            entities["fact_type"]
        )

    if intent == "get_definition":
        return get_definition(entities["topic"])

    if intent == "get_tips":
        return get_tips(entities["topic"])


# ============================================================================
# VALIDATION & CLARIFICATION
# ============================================================================

def ask_for_clarification():
    """Called when confidence is low or intent is unknown."""
    return {
        "status": "needs_clarification",
        "message": "I'm not sure what you want to do. Could you rephrase that?"
    }


def validate_entities(intent, entities):
    """
    Validates that all required entities for the given intent are present.
    Raises ValueError if validation fails.
    """
    import json
    
    # Load entity requirements
    with open("entities.json", "r") as f:
        entity_schema = json.load(f)
    
    if intent not in entity_schema:
        raise ValueError(f"Unknown intent: {intent}")
    
    required = entity_schema[intent]["required"]
    
    # Check all required entities are present
    missing = [e for e in required if e not in entities]
    
    if missing:
        raise ValueError(
            f"Missing required entities for '{intent}': {', '.join(missing)}"
        )


# ============================================================================
# EXECUTORS
# ============================================================================

def open_application(application):
    """Opens the specified application."""
    return {
        "status": "success",
        "action": "open_application",
        "application": application,
        "message": f"Opening {application}..."
    }


def open_application_and_navigate(application, url):
    """Opens the specified application and navigates to a URL."""
    return {
        "status": "success",
        "action": "open_application_and_navigate",
        "application": application,
        "url": url,
        "message": f"Opening {application} and navigating to {url}..."
    }


def play_music(song, artist=None):
    """Plays the specified song, optionally filtering by artist."""
    if artist:
        return {
            "status": "success",
            "action": "play_music",
            "song": song,
            "artist": artist,
            "message": f"Playing '{song}' by {artist}..."
        }
    else:
        return {
            "status": "success",
            "action": "play_music",
            "song": song,
            "message": f"Playing '{song}'..."
        }


def get_weather(location):
    """Retrieves weather information for the specified location."""
    return {
        "status": "success",
        "action": "get_weather",
        "location": location,
        "message": f"Fetching weather for {location}..."
    }


def get_fact(subject, fact_type):
    """Retrieves a fact about the specified subject."""
    return {
        "status": "success",
        "action": "get_fact",
        "subject": subject,
        "fact_type": fact_type,
        "message": f"Fetching a {fact_type} fact about {subject}..."
    }


def get_definition(topic):
    """Retrieves the definition of the specified topic."""
    return {
        "status": "success",
        "action": "get_definition",
        "topic": topic,
        "message": f"Fetching definition for '{topic}'..."
    }


def get_tips(topic):
    """Retrieves tips about the specified topic."""
    return {
        "status": "success",
        "action": "get_tips",
        "topic": topic,
        "message": f"Fetching tips for '{topic}'..."
    }
