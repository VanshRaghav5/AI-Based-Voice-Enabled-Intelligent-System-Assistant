"""
Tests for Confidence Configuration

Tests threshold management and decision logic.
"""

import pytest
import json
import os
import tempfile
from backend.core.confidence_config import ConfidenceConfig


@pytest.fixture
def temp_config_file():
    """Create temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        return f.name


@pytest.fixture
def config(temp_config_file):
    """Create config with temporary file."""
    return ConfidenceConfig(config_file=temp_config_file)


def test_config_initialization(config):
    """Test config initializes with defaults."""
    assert config.high_confidence_threshold == 0.8
    assert config.medium_confidence_threshold == 0.5
    assert config.low_confidence_threshold == 0.3
    assert config.auto_execute_threshold == 0.8


def test_should_auto_execute(config):
    """Test auto-execute decision."""
    assert config.should_auto_execute(0.9) == True
    assert config.should_auto_execute(0.8) == True
    assert config.should_auto_execute(0.7) == False


def test_should_confirm(config):
    """Test confirmation decision."""
    assert config.should_confirm(0.9) == False  # Too high
    assert config.should_confirm(0.6) == False  # Too high
    assert config.should_confirm(0.4) == True   # In confirm range
    assert config.should_confirm(0.1) == False  # Below reject threshold


def test_should_reject(config):
    """Test rejection decision."""
    assert config.should_reject(0.9) == False
    assert config.should_reject(0.5) == False
    assert config.should_reject(0.2) == False  # Default reject is 0.2
    assert config.should_reject(0.1) == True


def test_classify_confidence_high(config):
    """Test high confidence classification."""
    assert config.classify_confidence(0.9) == "high"
    assert config.classify_confidence(0.8) == "high"


def test_classify_confidence_medium(config):
    """Test medium confidence classification."""
    assert config.classify_confidence(0.7) == "medium"
    assert config.classify_confidence(0.5) == "medium"


def test_classify_confidence_low(config):
    """Test low confidence classification."""
    assert config.classify_confidence(0.4) == "low"
    assert config.classify_confidence(0.3) == "low"


def test_classify_confidence_very_low(config):
    """Test very low confidence classification."""
    assert config.classify_confidence(0.2) == "very_low"
    assert config.classify_confidence(0.1) == "very_low"


def test_get_action_execute(config):
    """Test execute action recommendation."""
    assert config.get_action(0.9) == "execute"
    assert config.get_action(0.85) == "execute"


def test_get_action_confirm(config):
    """Test confirm action recommendation."""
    assert config.get_action(0.6) == "confirm"
    assert config.get_action(0.4) == "confirm"


def test_get_action_clarify(config):
    """Test clarify action recommendation."""
    # Note: clarify is for medium-low but above reject
    assert config.get_action(0.7) == "confirm"


def test_get_action_reject(config):
    """Test reject action recommendation."""
    assert config.get_action(0.1) == "reject"


def test_update_threshold(config):
    """Test updating threshold value."""
    config.update_threshold("high_confidence", 0.85)
    
    assert config.high_confidence_threshold == 0.85


def test_update_threshold_invalid_range(config):
    """Test updating threshold with invalid value."""
    with pytest.raises(ValueError):
        config.update_threshold("high_confidence", 1.5)
    
    with pytest.raises(ValueError):
        config.update_threshold("high_confidence", -0.1)


def test_update_threshold_unknown(config):
    """Test updating unknown threshold."""
    with pytest.raises(ValueError):
        config.update_threshold("nonexistent", 0.5)


def test_update_behavior_threshold(config):
    """Test updating behavior threshold."""
    config.update_threshold("auto_execute_above", 0.75)
    
    assert config.auto_execute_threshold == 0.75
    assert config.should_auto_execute(0.8) == True
    assert config.should_auto_execute(0.7) == False


def test_reset_to_defaults(config):
    """Test resetting to default configuration."""
    # Change some values
    config.update_threshold("high_confidence", 0.9)
    assert config.high_confidence_threshold == 0.9
    
    # Reset
    config.reset_to_defaults()
    
    # Should be back to defaults
    assert config.high_confidence_threshold == 0.8


def test_persistence(temp_config_file):
    """Test configuration persists to disk."""
    # Create config and update
    config1 = ConfidenceConfig(config_file=temp_config_file)
    config1.update_threshold("high_confidence", 0.85)
    
    # Create new config with same file
    config2 = ConfidenceConfig(config_file=temp_config_file)
    
    # Should load previous value
    assert config2.high_confidence_threshold == 0.85


def test_default_config_structure(config):
    """Test default config has all required sections."""
    assert "thresholds" in config.config
    assert "behavior" in config.config
    assert "logging" in config.config
    assert "analytics" in config.config
    
    # Check threshold keys
    assert "high_confidence" in config.config["thresholds"]
    assert "medium_confidence" in config.config["thresholds"]
    assert "low_confidence" in config.config["thresholds"]
    
    # Check behavior keys
    assert "auto_execute_above" in config.config["behavior"]
    assert "always_confirm_below" in config.config["behavior"]
    assert "reject_below" in config.config["behavior"]


def test_threshold_cascade(config):
    """Test threshold ordering makes sense."""
    # High > Medium > Low
    assert config.high_confidence_threshold > config.medium_confidence_threshold
    assert config.medium_confidence_threshold > config.low_confidence_threshold
    
    # Auto-execute >= High confidence
    assert config.auto_execute_threshold >= config.high_confidence_threshold


def test_edge_case_exact_threshold(config):
    """Test behavior at exact threshold values."""
    # Exactly at auto-execute threshold
    assert config.should_auto_execute(0.8) == True
    
    # Exactly at medium threshold
    assert config.classify_confidence(0.5) == "medium"


def test_logging_settings(config):
    """Test logging configuration settings."""
    assert config.config["logging"]["log_all_confidence"] == True
    assert config.config["logging"]["alert_on_very_low"] == True
    assert config.config["logging"]["very_low_threshold"] == 0.3


def test_analytics_settings(config):
    """Test analytics configuration settings."""
    assert config.config["analytics"]["track_history"] == True
    assert config.config["analytics"]["max_history_size"] == 1000
    assert config.config["analytics"]["calculate_trends"] == True


def test_custom_threshold_workflow(config):
    """Test realistic workflow with custom thresholds."""
    # Scenario: Stricter system - higher thresholds
    config.update_threshold("auto_execute_above", 0.9)
    config.update_threshold("always_confirm_below", 0.7)
    config.update_threshold("reject_below", 0.3)
    
    # High confidence command
    assert config.get_action(0.95) == "execute"
    
    # Medium-high confidence - needs confirmation now
    assert config.get_action(0.8) == "confirm"
    
    # Low confidence - reject
    assert config.get_action(0.25) == "reject"


def test_lenient_threshold_workflow(config):
    """Test lenient workflow with lower thresholds."""
    # Scenario: Lenient system - lower thresholds
    config.update_threshold("auto_execute_above", 0.6)
    config.update_threshold("always_confirm_below", 0.4)
    config.update_threshold("reject_below", 0.1)
    
    # Medium confidence auto-executes
    assert config.get_action(0.7) == "execute"
    
    # Lower confidence still confirms
    assert config.get_action(0.3) == "confirm"
    
    # Very low rejects
    assert config.get_action(0.05) == "reject"
