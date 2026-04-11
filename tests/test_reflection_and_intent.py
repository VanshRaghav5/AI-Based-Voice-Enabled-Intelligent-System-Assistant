"""Tests for reflection, natural responses, and optional intent classification."""
from __future__ import annotations

from unittest.mock import Mock

import pytest

from backend.core.execution.reflection import ReflectionEngine
from backend.core.execution.response_generator import ResponseGenerator
from backend.core.intent.classifier import IntentClassifier
from backend.core.memory.memory_manager import MemoryManager
from backend.core.planner.schema import Plan, Step


def test_reflection_engine_recommends_retry_for_port_busy():
    engine = ReflectionEngine()

    result = engine.analyze({"success": False, "error": "Port 8080 is busy"})

    assert result["retry"] is True
    assert result["should_replan"] is True
    assert "port" in result["suggestion"].lower()


def test_response_generator_uses_natural_language():
    generator = ResponseGenerator()
    plan = Plan("Start work session", [Step(0, "open_app", {"app_name": "code"}), Step(1, "run_command", {"command": "jupyter notebook"})])

    message = generator.generate("Start my ML work", plan, {"success": True, "message": "Command completed"})

    assert "completed" in message.lower()
    assert "open app" in message.lower() or "run command" in message.lower()


def test_memory_manager_tracks_active_goal(tmp_path):
    memory = MemoryManager(long_term_file_path=str(tmp_path / "memory.json"))

    memory.set("active_goal", "ML project")

    assert memory.get("active_goal") == "ML project"


def test_intent_classifier_optional_llm_path(monkeypatch):
    classifier = IntentClassifier()

    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "response": '{"intent": "debug_error", "confidence": 0.93}'
    }

    fake_post = Mock(return_value=fake_response)
    monkeypatch.setattr("backend.core.intent.classifier.requests.post", fake_post)

    result = classifier.classify("this app throws an exception", use_llm=True)

    assert result["intent"] == "debug_error"
    assert result["confidence"] == 0.93
    assert result["source"] == "llm"
