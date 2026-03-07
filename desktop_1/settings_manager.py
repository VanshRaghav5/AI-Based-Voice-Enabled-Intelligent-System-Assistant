"""Settings manager for desktop UI."""
import json
from pathlib import Path


class SettingsManager:
    """Manage UI settings (theme, preferences, etc.)."""
    
    def __init__(self):
        """Initialize settings manager."""
        self.config_dir = Path.home() / ".omniassist"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "ui_settings.json"
        self.default_settings = {
            "theme": "dark",  # dark or light
            "persona": "friendly",
            "language": "hinglish",
            "memory_enabled": True,
            "auto_listen": False,
            "font_size": 11,
        }
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from file or use defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to handle new settings
                    settings = {**self.default_settings, **loaded}
                    return settings
            except Exception as e:
                print(f"Error loading settings: {e}, using defaults")
                return self.default_settings.copy()
        return self.default_settings.copy()
    
    def save(self):
        """Save settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set a setting value and save."""
        self.settings[key] = value
        self.save()
    
    def get_all(self) -> dict:
        """Get all settings."""
        return self.settings.copy()


# Global settings instance
settings_manager = SettingsManager()
