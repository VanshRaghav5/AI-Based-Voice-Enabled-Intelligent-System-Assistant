"""
Tests for Confidence Tracker

Tests confidence score recording, statistics, and analytics.
"""

import pytest
import json
import os
import tempfile
from datetime import datetime
from backend.core.confidence_tracker import ConfidenceTracker, ConfidenceEntry


@pytest.fixture
def temp_history_file():
    """Create temporary history file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        return f.name


@pytest.fixture
def tracker(temp_history_file):
    """Create tracker with temporary file."""
    return ConfidenceTracker(history_file=temp_history_file)


def test_tracker_initialization(tracker):
    """Test tracker initializes correctly."""
    assert tracker.history == []
    assert tracker.max_history_size == 1000
    assert os.path.exists(tracker.history_file)


def test_record_confidence(tracker):
    """Test recording confidence entries."""
    tracker.record(
        command="create file report.txt",
        intent="file.create",
        confidence=0.85,
        source="ollama",
        executed=True,
        needed_clarification=False,
        validation_passed=True
    )
    
    assert len(tracker.history) == 1
    entry = tracker.history[0]
    
    assert entry.command == "create file report.txt"
    assert entry.intent == "file.create"
    assert entry.confidence == 0.85
    assert entry.source == "ollama"
    assert entry.executed == True
    assert entry.needed_clarification == False
    assert entry.validation_passed == True
    assert entry.timestamp is not None


def test_multiple_records(tracker):
    """Test recording multiple entries."""
    for i in range(5):
        tracker.record(
            command=f"command {i}",
            intent="test",
            confidence=0.5 + (i * 0.1),
            source="ollama",
            executed=True
        )
    
    assert len(tracker.history) == 5
    assert tracker.history[0].confidence == 0.5
    assert tracker.history[4].confidence == 0.9


def test_history_size_limit(tracker):
    """Test history size is limited."""
    tracker.max_history_size = 10
    
    # Add 15 entries
    for i in range(15):
        tracker.record(
            command=f"cmd {i}",
            intent="test",
            confidence=0.5,
            source="ollama"
        )
    
    # Should only keep last 10
    assert len(tracker.history) == 10
    assert tracker.history[0].command == "cmd 5"  # First 5 removed


def test_get_statistics_empty(tracker):
    """Test statistics with no data."""
    stats = tracker.get_statistics()
    
    assert stats['total_commands'] == 0
    assert stats['avg_confidence'] == 0.0


def test_get_statistics_with_data(tracker):
    """Test statistics calculation."""
    # Add entries with known confidences
    confidences = [0.9, 0.7, 0.5, 0.3, 0.1]
    for conf in confidences:
        tracker.record(
            command="test",
            intent="test",
            confidence=conf,
            source="ollama",
            executed=conf >= 0.5
        )
    
    stats = tracker.get_statistics()
    
    assert stats['total_commands'] == 5
    assert stats['avg_confidence'] == 0.5  # (0.9+0.7+0.5+0.3+0.1)/5
    assert stats['min_confidence'] == 0.1
    assert stats['max_confidence'] == 0.9
    assert stats['executed_count'] == 3  # 0.9, 0.7, 0.5


def test_statistics_by_source(tracker):
    """Test statistics breakdown by source."""
    # Add ollama entries
    for _ in range(3):
        tracker.record("test", "test", 0.8, "ollama", executed=True)
    
    # Add fallback entries
    for _ in range(2):
        tracker.record("test", "test", 0.4, "fallback", executed=False)
    
    stats = tracker.get_statistics()
    
    assert stats['ollama_count'] == 3
    assert stats['fallback_count'] == 2
    assert stats['ollama_avg_confidence'] > stats['fallback_avg_confidence']


def test_confidence_distribution(tracker):
    """Test confidence distribution calculation."""
    # Add entries across all ranges
    tracker.record("test", "test", 0.9, "ollama")  # High
    tracker.record("test", "test", 0.6, "ollama")  # Medium
    tracker.record("test", "test", 0.4, "ollama")  # Low
    
    stats = tracker.get_statistics()
    
    assert stats['high_confidence_count'] == 1  # >= 0.8
    assert stats['medium_confidence_count'] == 1  # 0.5-0.8
    assert stats['low_confidence_count'] == 1  # < 0.5


def test_get_low_confidence_commands(tracker):
    """Test filtering low confidence commands."""
    tracker.record("high conf", "test", 0.9, "ollama")
    tracker.record("low conf 1", "test", 0.3, "fallback", executed=False)
    tracker.record("low conf 2", "test", 0.2, "fallback", executed=False)
    
    low_conf = tracker.get_low_confidence_commands(threshold=0.5)
    
    assert len(low_conf) == 2
    assert all(e.confidence < 0.5 for e in low_conf)


def test_intent_confidence_map(tracker):
    """Test intent-based confidence mapping."""
    tracker.record("create file", "file.create", 0.9, "ollama")
    tracker.record("delete file", "file.delete", 0.7, "ollama")
    tracker.record("another create", "file.create", 0.8, "ollama")
    
    intent_map = tracker.get_intent_confidence_map()
    
    assert "file.create" in intent_map
    assert "file.delete" in intent_map
    
    assert intent_map["file.create"]["count"] == 2
    assert intent_map["file.create"]["avg"] == 0.85  # (0.9+0.8)/2
    assert intent_map["file.delete"]["count"] == 1
    assert intent_map["file.delete"]["avg"] == 0.7


def test_get_recent_entries(tracker):
    """Test getting recent entries."""
    for i in range(10):
        tracker.record(f"cmd {i}", "test", 0.5, "ollama")
    
    recent = tracker.get_recent_entries(5)
    
    assert len(recent) == 5
    assert recent[0].command == "cmd 5"  # Most recent 5
    assert recent[4].command == "cmd 9"


def test_persistence(temp_history_file):
    """Test data persists to disk."""
    # Create tracker and add data
    tracker1 = ConfidenceTracker(history_file=temp_history_file)
    tracker1.record("test command", "test", 0.8, "ollama")
    
    # Create new tracker with same file
    tracker2 = ConfidenceTracker(history_file=temp_history_file)
    
    # Should load previous data
    assert len(tracker2.history) == 1
    assert tracker2.history[0].command == "test command"


def test_export_to_json(tracker, tmp_path):
    """Test exporting history to JSON."""
    tracker.record("test", "test", 0.8, "ollama")
    
    export_file = tmp_path / "export.json"
    tracker.export_to_json(str(export_file))
    
    # Verify file exists and has valid JSON
    assert export_file.exists()
    with open(export_file, 'r') as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]['command'] == "test"


def test_trend_analysis_insufficient_data(tracker):
    """Test trend analysis with insufficient data."""
    # Add only 5 entries (less than window size of 50)
    for i in range(5):
        tracker.record("test", "test", 0.5, "ollama")
    
    trend = tracker.get_trend_analysis()
    
    assert trend['trend'] == 'insufficient_data'


def test_trend_analysis_improving(tracker):
    """Test detecting improving trend."""
    # First window: low confidence
    for _ in range(30):
        tracker.record("test", "test", 0.4, "ollama")
    
    # Second window: high confidence
    for _ in range(30):
        tracker.record("test", "test", 0.8, "ollama")
    
    trend = tracker.get_trend_analysis(window_size=30)
    
    assert trend['trend'] == 'improving'
    assert trend['change'] > 0


def test_trend_analysis_declining(tracker):
    """Test detecting declining trend."""
    # First window: high confidence
    for _ in range(30):
        tracker.record("test", "test", 0.8, "ollama")
    
    # Second window: low confidence
    for _ in range(30):
        tracker.record("test", "test", 0.4, "ollama")
    
    trend = tracker.get_trend_analysis(window_size=30)
    
    assert trend['trend'] == 'declining'
    assert trend['change'] < 0


def test_clarification_tracking(tracker):
    """Test tracking clarification needs."""
    tracker.record("clear", "test", 0.9, "ollama", executed=True, needed_clarification=False)
    tracker.record("unclear", "test", 0.3, "fallback", executed=False, needed_clarification=True)
    
    stats = tracker.get_statistics()
    
    assert stats['clarification_count'] == 1
    assert stats['clarification_percentage'] == 50.0


def test_validation_tracking(tracker):
    """Test tracking validation results."""
    tracker.record("valid", "test", 0.8, "ollama", validation_passed=True)
    tracker.record("invalid", "test", 0.5, "ollama", validation_passed=False)
    
    assert tracker.history[0].validation_passed == True
    assert tracker.history[1].validation_passed == False
