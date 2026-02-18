# Ollama Intent Engine

A local intent classification and entity extraction system powered by a custom Ollama model (LLaMA 3 8B). It parses natural-language user commands into structured JSON, then routes them to the appropriate executor via a planner.

## Architecture

```
User Command
     │
     ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Prompt  │───▶│  Ollama  │───▶│ Planner  │───▶ Executor
│ Template │    │  Model   │    │ (Router) │
└──────────┘    └──────────┘    └──────────┘
                                     │
                              ┌──────┴──────┐
                              │  Entities   │
                              │  Validation │
                              └─────────────┘
```

1. **Prompt** (`prompt.txt`) — Instructs the LLM to classify the user's command into an intent and extract entities.
2. **Model** (`Modelfile`) — A deterministic Ollama model built on `llama3:8b` with low temperature/top-p to ensure consistent, JSON-only output.
3. **Planner** (`planner.py`) — Validates the LLM response (confidence, entities) and dispatches to the correct executor function.

## Files

| File | Purpose |
| --- | --- |
| `Modelfile` | Ollama model definition — base model, parameters, and system prompts |
| `prompt.txt` | Prompt template sent to the model with the user's command |
| `entities.json` | Schema defining required/optional entities per intent |
| `intent.md` | Frozen intent taxonomy — the single source of truth for allowed intents |
| `planner.py` | Decision engine that validates and routes LLM output to executors |

## Supported Intents

| Intent | Required Entities | Optional Entities | Example |
| --- | --- | --- | --- |
| `open_application` | `application` | — | *"Open Spotify"* |
| `open_application_and_navigate` | `application`, `url` | — | *"Open Chrome and go to YouTube"* |
| `play_music` | `song` | `artist` | *"Play Bohemian Rhapsody by Queen"* |
| `get_weather` | `location` | — | *"What's the weather in Tokyo?"* |
| `get_fact` | `subject`, `fact_type` | — | *"Tell me a fun fact about Mars"* |
| `get_definition` | `topic` | — | *"Define machine learning"* |
| `get_tips` | `topic` | — | *"Give me tips on public speaking"* |
| `unknown` | — | — | Anything that doesn't match above |

## Model Configuration

Defined in `Modelfile`:

| Parameter | Value | Reason |
| --- | --- | --- |
| `temperature` | 0.0 | Deterministic output — no creativity needed |
| `top_p` | 0.5 | Narrow token sampling for consistency |
| `repeat_penalty` | 1.2 | Prevents repetitive tokens in output |
| `num_ctx` | 2048 | Context window size |

The model is constrained via system prompts to:

- Output **only** valid JSON (no markdown, no explanations)
- Cap confidence between **0.0 and 0.95** (never 1.0)

## LLM Output Schema

The model returns a single JSON object:

```json
{
  "intent": "open_application_and_navigate",
  "entities": {
    "application": "chrome",
    "url": "https://www.youtube.com"
  },
  "confidence": 0.92
}
```

## Planner Logic

`planner.py` processes the LLM output through these steps:

1. **Confidence check** — If `confidence < 0.7`, ask for clarification.
2. **Unknown intent** — If intent is `unknown`, ask for clarification.
3. **Entity validation** — Checks that all required entities (defined in `entities.json`) are present.
4. **Dispatch** — Routes to the matching executor function (e.g., `open_application()`, `play_music()`).

## Setup

### Prerequisites

- [Ollama](https://ollama.com/) installed and running locally

### Create the Model

```bash
ollama create intent-engine -f Modelfile
```

### Run a Query

```bash
ollama run intent-engine "Open Chrome and go to YouTube"
```

The model will return a JSON object that can be passed directly to `planner.plan()`.

## Adding a New Intent

1. Add the intent name to `intent.md`.
2. Define its required/optional entities in `entities.json`.
3. Add a handler branch in `planner.py`.
4. Update the `ALLOWED INTENTS` list in `prompt.txt`.
5. Implement the corresponding executor function.
