"""Tests for the basic rule-based intent classifier."""
import pytest

from backend.core.intent.classifier import IntentClassifier


@pytest.fixture
def classifier():
    return IntentClassifier()


@pytest.mark.parametrize(
    "text, expected_intent, min_confidence",
    [
        ("start work session", "start_work_session", 0.9),
        ("please organize these files", "organize_files", 0.85),
        ("run the cleanup command", "run_command", 0.8),
        ("open notepad", "open_app", 0.8),
        ("search the web for python decorators", "search_web", 0.82),
    ],
)
def test_classify_known_intents(classifier, text, expected_intent, min_confidence):
    result = classifier.classify(text)

    assert result["intent"] == expected_intent
    assert result["confidence"] >= min_confidence
    assert result["matched_keywords"]


def test_classify_unknown_intent(classifier):
    result = classifier.classify("tell me a joke")

    assert result["intent"] == "unknown"
    assert result["confidence"] == 0.5
    assert result["matched_keywords"] == []


def test_classify_empty_input_returns_unknown(classifier):
    result = classifier.classify("   ")

    assert result["intent"] == "unknown"
    assert result["confidence"] == 0.5
    assert result["matched_keywords"] == []


def test_classify_prefers_first_matching_rule(classifier):
    result = classifier.classify("open and search the web")

    assert result["intent"] == "open_app"
    assert result["confidence"] == 0.8
