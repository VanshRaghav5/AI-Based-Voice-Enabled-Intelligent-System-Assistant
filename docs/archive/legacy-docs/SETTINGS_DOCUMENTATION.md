# Settings System - Documentation

**Version**: 1.0  
**Date**: March 6, 2026

---

## Overview

The OmniAssist UI now includes a comprehensive **Settings Modal** accessible from the top-right corner (⚙️ button). All settings are persistent and automatically saved to the user's home directory.

---

## Settings Categories

### 🎨 Appearance
- **Theme**: Toggle between Light and Dark modes
  - Dark mode: Better for low-light environments (default)
  - Light mode: Better for bright environments
  - Changes apply on app restart
  - Radio buttons for easy selection

- **Font Size**: Adjustable from 9pt to 16pt
  - Slider control
  - Live preview (shows current size)
  - Affects all text elements

### 🎭 Assistant

- **Persona**: Choose assistant personality
  - Options: Friendly, Professional, Concise, Formal
  - Affects LLM response style and tone
  - Saves to local config
  - Real-time selection via dropdown

- **Language**: Select communication language
  - Options: English, Hindi, Hinglish
  - Affects both STT and TTS
  - Dropdown menu for easy switching
  - Changes take effect immediately

### ⚙️ Features

- **💾 Conversation Memory**: Toggle
  - ON: Assistant remembers conversation history
  - OFF: Each command starts fresh
  - Switch on/off with toggle button
  - Affects backend memory integration

- **🎙️ Auto-Listen on Start**: Toggle
  - ON: App automatically starts listening when opened
  - OFF: Manual "Start Listening" required
  - Useful for hands-free operation
  - Saved to local config

### ℹ️ About
- App version and description
- Read-only information section

---

## Settings Storage

### Location
Settings are stored in: `~/.omniassist/ui_settings.json`
- Windows: `C:\Users\<username>\.omniassist\ui_settings.json`
- Linux/Mac: `~/.omniassist/ui_settings.json`

### Format
```json
{
  "theme": "dark",
  "persona": "friendly",
  "language": "hinglish",
  "memory_enabled": true,
  "auto_listen": false,
  "font_size": 11
}
```

### Persistence
- Settings are automatically saved when changed
- File is created on first run
- Persists across app restarts

---

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ Settings                                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 🎨 Appearance                                          │
│   Theme:     ○ Light   ◉ Dark                         │
│   Font Size: [━━━━●━━━━━━] 11pt                        │
│                                                         │
│ 🎭 Assistant                                           │
│   Persona:   [friendly ▼]                              │
│   Language:  [hinglish ▼]                              │
│                                                         │
│ ⚙️ Features                                            │
│   💾 Conversation Memory      [●───]                   │
│   🎙️ Auto-Listen on Start    [───○]                   │
│                                                         │
│ ℹ️ About                                               │
│   OmniAssist AI v1.0                                   │
│   Voice-Enabled Desktop Automation                     │
│                                                         │
│              [Save & Close]  [Reset to Defaults]      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## How to Access Settings

1. **Click the ⚙️ button** in the top-right corner of the main UI
2. **Settings Modal** opens (500x600px, non-resizable)
3. **Adjust settings** using dropdowns, sliders, toggles, and radio buttons
4. **Click "Save & Close"** to apply and close
5. **Or "Reset to Defaults"** to revert all settings to initial state

---

## Feature Integration

### Persona
- Sent to backend via `/api/process_command`
- Affects LLM prompt and response generation
- Available options: friendly, professional, concise, formal

### Language
- Controls Whisper STT language model
- Affects Piper TTS voice generation
- Supported: English, Hindi, Hinglish (mixed English-Hindi)

### Memory
- When enabled: Backend stores conversation history
- When disabled: Each command is independent
- Can be toggled during runtime

### Auto-Listen
- Intended for future implementation
- Currently saved but not actively used
- Will auto-start voice listener on app launch

### Theme
- **Dark Mode**: 
  - App closes and restarts with dark theme
  - Better for evening/night use
  - Reduces eye strain in dark environments

- **Light Mode**:
  - App closes and restarts with light theme
  - Better for daytime use
  - Higher contrast for better readability

### Font Size
- Applied to all text elements in real-time
- Range: 9pt to 16pt
- Useful for accessibility

---

## Technical Implementation

### SettingsManager (`desktop_1/settings_manager.py`)
```python
# Initialize
from settings_manager import settings_manager

# Get a setting
value = settings_manager.get("theme")

# Set a setting (auto-saves)
settings_manager.set("theme", "light")

# Get all settings
all_settings = settings_manager.get_all()
```

### SettingsModal (`desktop_1/ui/settings_modal.py`)
```python
# Open settings modal
from ui.settings_modal import SettingsModal

modal = SettingsModal(parent_window, settings_manager)
modal.on_settings_changed = callback_function
```

### ChatWindow Integration
```python
def _open_settings(self):
    """Open the settings modal."""
    settings_window = SettingsModal(self.master_window, self.settings_manager)
    settings_window.on_settings_changed = self._on_settings_changed
```

---

## User Guidelines

### Best Practices
1. **Use Dark Mode for evening use** - reduces eye strain
2. **Adjust font size to your preference** - improves readability
3. **Choose persona that matches your workflow** - affects response tone
4. **Select language you're comfortable with** - improves STT accuracy
5. **Enable memory for multi-turn conversations** - maintains context

### Troubleshooting

**Settings not saving?**
- Check permissions on `~/.omniassist/` folder
- Ensure disk space is available
- Try resetting to defaults

**Theme changes not applying?**
- Close all instances of OmniAssist
- Check if `.ui_settings.json` is readable
- Try manual edit of the settings file

**Font size too small/large?**
- Use the slider in Settings modal
- Adjust and click Save & Close
- Changes apply on next app restart

---

## Future Enhancements

- [ ] Per-command language selection
- [ ] Custom persona creation
- [ ] Keyboard shortcuts for settings
- [ ] Settings import/export
- [ ] Per-contact language preferences (for WhatsApp)
- [ ] Custom color themes
- [ ] Advanced LLM parameter tuning
- [ ] Auto-language detection for input

---

## Testing Checklist

- [ ] Settings modal opens from ⚙️ button
- [ ] All settings dropdowns work
- [ ] Theme toggle saves correctly
- [ ] Font size slider functional
- [ ] Memory toggle works
- [ ] Settings persist after restart
- [ ] Reset to defaults works
- [ ] Dark mode UI is readable
- [ ] Light mode UI is readable
- [ ] Settings JSON created in home directory

---

**Documentation Complete**

---

For implementation details, see:
- `desktop_1/settings_manager.py` - Settings persistence
- `desktop_1/ui/settings_modal.py` - UI implementation
- `desktop_1/ui/chat_window.py` - Integration with main UI
- `desktop_1/main.py` - Theme initialization
