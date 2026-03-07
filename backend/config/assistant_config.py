import json
import os
from typing import Any, Dict

from backend.config.logger import logger


DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "assistant_config.json")


class AssistantConfig:

    def __init__(self, path: str = DEFAULT_CONFIG_PATH):
        self.path = path
        self.data: Dict[str, Any] = {}
        self.reload()

    def reload(self):
        try:
            if not os.path.exists(self.path):
                logger.warning(f"[Config] Config file not found: {self.path}")
                self.data = {}
                return

            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            logger.info(f"[Config] Loaded assistant config from: {self.path}")
        except Exception as exc:
            logger.error(f"[Config] Failed to load config: {exc}")
            self.data = {}

    def get(self, dotted_path: str, default: Any = None) -> Any:
        current = self.data
        for part in dotted_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, dotted_path: str, value: Any) -> bool:
        """Update a config value and save to disk.
        
        Args:
            dotted_path: Path to the config value (e.g., 'assistant.active_persona')
            value: New value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            parts = dotted_path.split(".")
            current = self.data
            
            # Navigate to the parent of the target key
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value
            current[parts[-1]] = value
            
            # Save to disk
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[Config] Updated {dotted_path} = {value}")
            return True
        except Exception as exc:
            logger.error(f"[Config] Failed to update {dotted_path}: {exc}")
            return False


assistant_config = AssistantConfig()
