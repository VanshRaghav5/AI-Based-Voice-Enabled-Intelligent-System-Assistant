"""
Confidence Configuration

Configurable thresholds and settings for the confidence system.
"""

import os
import json
import copy
from typing import Dict, Any
from backend.utils.logger import logger


class ConfidenceConfig:
    """
    Configuration for confidence-based decision making.
    
    Thresholds determine when to execute vs clarify.
    """
    
    # Default thresholds
    DEFAULT_CONFIG = {
        "thresholds": {
            "high_confidence": 0.8,      # Execute without confirmation
            "medium_confidence": 0.5,    # Ask for confirmation
            "low_confidence": 0.3,       # Request clarification
        },
        "behavior": {
            "auto_execute_above": 0.8,   # Auto-execute if confidence above this
            "always_confirm_below": 0.5,  # Always confirm if confidence below this
            "reject_below": 0.2,         # Don't execute if confidence below this
        },
        "logging": {
            "log_all_confidence": True,
            "log_low_confidence_only": False,
            "alert_on_very_low": True,
            "very_low_threshold": 0.3,
        },
        "analytics": {
            "track_history": True,
            "max_history_size": 1000,
            "calculate_trends": True,
        }
    }
    
    def __init__(self, config_file: str = None):
        """
        Initialize confidence configuration.
        
        Args:
            config_file: Path to config JSON file (optional)
        """
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(__file__),
                "..", "..",
                "data",
                "confidence_config.json"
            )
        
        self.config_file = os.path.abspath(config_file)
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Load config if exists
        self._load_config()
    
    @property
    def high_confidence_threshold(self) -> float:
        """Get high confidence threshold."""
        return self.config["thresholds"]["high_confidence"]
    
    @property
    def medium_confidence_threshold(self) -> float:
        """Get medium confidence threshold."""
        return self.config["thresholds"]["medium_confidence"]
    
    @property
    def low_confidence_threshold(self) -> float:
        """Get low confidence threshold."""
        return self.config["thresholds"]["low_confidence"]
    
    @property
    def auto_execute_threshold(self) -> float:
        """Get auto-execute threshold."""
        return self.config["behavior"]["auto_execute_above"]
    
    @property
    def always_confirm_threshold(self) -> float:
        """Get always-confirm threshold."""
        return self.config["behavior"]["always_confirm_below"]
    
    @property
    def reject_threshold(self) -> float:
        """Get reject threshold."""
        return self.config["behavior"]["reject_below"]
    
    def should_auto_execute(self, confidence: float) -> bool:
        """Determine if command should auto-execute based on confidence."""
        return confidence >= self.auto_execute_threshold
    
    def should_confirm(self, confidence: float) -> bool:
        """Determine if confirmation is needed."""
        return confidence < self.always_confirm_threshold and confidence >= self.reject_threshold
    
    def should_reject(self, confidence: float) -> bool:
        """Determine if command should be rejected."""
        return confidence < self.reject_threshold
    
    def classify_confidence(self, confidence: float) -> str:
        """
        Classify confidence level.
        
        Returns:
            "high", "medium", "low", or "very_low"
        """
        if confidence >= self.high_confidence_threshold:
            return "high"
        elif confidence >= self.medium_confidence_threshold:
            return "medium"
        elif confidence >= self.low_confidence_threshold:
            return "low"
        else:
            return "very_low"
    
    def get_action(self, confidence: float) -> str:
        """
        Get recommended action based on confidence.
        
        Returns:
            "execute", "confirm", "clarify", or "reject"
        """
        if self.should_reject(confidence):
            return "reject"
        elif confidence >= self.auto_execute_threshold:
            return "execute"
        elif confidence >= self.reject_threshold:
            return "confirm"
        else:
            return "clarify"
    
    def update_threshold(self, threshold_name: str, value: float) -> None:
        """
        Update a threshold value.
        
        Args:
            threshold_name: Name of threshold (e.g., "high_confidence")
            value: New threshold value (0.0 to 1.0)
        """
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {value}")
        
        if threshold_name in self.config["thresholds"]:
            self.config["thresholds"][threshold_name] = value
            logger.info(f"Updated threshold '{threshold_name}' to {value}")
            self._save_config()
        elif threshold_name in self.config["behavior"]:
            self.config["behavior"][threshold_name] = value
            logger.info(f"Updated behavior '{threshold_name}' to {value}")
            self._save_config()
        else:
            raise ValueError(f"Unknown threshold: {threshold_name}")
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        self._save_config()
        logger.info("Reset confidence configuration to defaults")
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults (in case new fields added)
                    for key in self.DEFAULT_CONFIG:
                        if key in loaded_config:
                            if isinstance(self.DEFAULT_CONFIG[key], dict):
                                self.config[key].update(loaded_config[key])
                            else:
                                self.config[key] = loaded_config[key]
                logger.info(f"Loaded confidence configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load confidence config: {e}, using defaults")
        else:
            # Save defaults
            self._save_config()
            logger.info("Created default confidence configuration")
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save confidence config: {e}")
    
    def print_config(self) -> None:
        """Print current configuration."""
        print("\n" + "="*70)
        print("CONFIDENCE CONFIGURATION")
        print("="*70)
        
        print("\nThresholds:")
        for key, value in self.config["thresholds"].items():
            print(f"  {key}: {value}")
        
        print("\nBehavior:")
        for key, value in self.config["behavior"].items():
            print(f"  {key}: {value}")
        
        print("\nLogging:")
        for key, value in self.config["logging"].items():
            print(f"  {key}: {value}")
        
        print("\nAnalytics:")
        for key, value in self.config["analytics"].items():
            print(f"  {key}: {value}")
        
        print("="*70 + "\n")


# Global instance
confidence_config = ConfidenceConfig()
