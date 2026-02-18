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
