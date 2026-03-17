# Examples

This directory contains standalone example scripts demonstrating various system components.

## Available Examples

### Command Parser Example
**File**: [example_command_parser.py](example_command_parser.py)

Demonstrates the command parsing system with interactive testing.

**Run**:
```bash
cd ..
python examples/example_command_parser.py
```

**Features**:
- Interactive command input
- Real-time parsing results
- Confidence score calculation
- Source tracking (Ollama vs Fallback)

---

### Confidence System Example
**File**: [example_confidence_system.py](example_confidence_system.py)

Demonstrates the confidence tracking and scoring system.

**Run**:
```bash
cd ..
python examples/example_confidence_system.py
```

**Features**:
- Confidence score calculation
- Multiple test scenarios
- LLM source detection
- Parameter extraction quality assessment
- Safety check demonstrations

---

## Quick Links
- Documentation: [../docs/](../docs/)
- Main README: [../README.md](../README.md)
- Backend Code: [../backend/](../backend/)
- Tests: [../tests/](../tests/)

---

## Runtime Notes

- The assistant now runs a bounded agent loop (`plan -> act -> observe -> replan`).
- Persistent memory is enabled by default in `backend/data/session_memory.json`.
- You can validate memory behavior from the app with commands like:
	- `Remember that office city is Pune`
	- `Recall office city`
	- Restart backend, then run `Recall office city` again
