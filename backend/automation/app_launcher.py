import subprocess
import os
import time
import tempfile

import pyperclip

from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.automation.window_detection import window_detector
from backend.config.logger import logger


APP_MAP = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe"
}


def open_app(app_name: str) -> dict:
    """
    Opens a desktop application with error handling.
    Returns structured response.
    """
    
    def _open():
        # Validate app name
        if not app_name or not app_name.strip():
            raise ValueError("Application name cannot be empty")
        
        app_name_lower = app_name.lower().strip()
        
        if app_name_lower not in APP_MAP:
            logger.warning(f"Application not in map: {app_name}")
            available_apps = ", ".join(APP_MAP.keys())
            raise AutomationError(
                f"Application '{app_name}' not found in app map",
                f"I don't know how to open '{app_name}'. I can open: {available_apps}"
            )
        
        app_path = APP_MAP[app_name_lower]
        
        logger.info(f"Opening application: {app_name} ({app_path})")
        
        try:
            # Check if the application exists (for full paths)
            if os.path.isabs(app_path) and not os.path.exists(app_path):
                logger.error(f"Application not found at path: {app_path}")
                raise FileNotFoundError(
                    f"Application not installed at: {app_path}"
                )
            
            # Launch the application
            subprocess.Popen(app_path, shell=True)
            
            # Wait a moment for the app to start
            import time
            time.sleep(1)
            
            # Try to detect if window opened (optional verification)
            # Note: This is best-effort, some apps may take longer
            
            return {
                "status": "success",
                "message": f"Opening {app_name}",
                "data": {"app": app_name, "path": app_path}
            }
            
        except FileNotFoundError as e:
            logger.error(f"Application not found: {e}")
            raise AutomationError(
                str(e),
                f"The {app_name} application is not installed on this computer."
            )
        except Exception as e:
            logger.error(f"Failed to open {app_name}: {e}")
            raise AutomationError(
                str(e),
                f"I couldn't open {app_name}. Please try opening it manually."
            )
    
    return error_handler.wrap_automation(
        func=_open,
        operation_name="Open Application",
        context={"app": app_name}
    )


def open_notepad_and_write(text: str) -> dict:
    """Open Notepad and write the provided text into the editor."""

    def _write():
        message = (text or "").strip()
        if not message:
            raise AutomationError(
                "Missing text for Notepad write",
                "I need text to write in Notepad.",
            )

        logger.info("[Notepad] Opening Notepad for text entry")
        subprocess.Popen(APP_MAP["notepad"], shell=True)

        # Allow process/window to initialize before sending input.
        time.sleep(1.1)
        window_detector.wait_for_window("Notepad", timeout=8)
        window_detector.focus_window("Notepad")
        time.sleep(0.25)

        try:
            import keyboard

            pyperclip.copy(message)
            keyboard.press_and_release("ctrl+v")
        except Exception as e:
            logger.warning(f"[Notepad] Clipboard paste failed, falling back to direct typing: {e}")
            try:
                import keyboard

                keyboard.write(message, delay=0.01)
            except Exception as type_err:
                logger.warning(f"[Notepad] Direct typing failed, using file-backed fallback: {type_err}")
                try:
                    temp_path = os.path.join(
                        tempfile.gettempdir(),
                        f"omniassist_note_{int(time.time())}.txt",
                    )
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(message)

                    subprocess.Popen(f'notepad.exe "{temp_path}"', shell=True)
                except Exception as fallback_err:
                    raise AutomationError(
                        f"Failed to enter text in Notepad: {fallback_err}",
                        "I opened Notepad but could not write the message.",
                    )

        return {
            "status": "success",
            "message": f"Opened Notepad and wrote {len(message)} characters",
            "data": {
                "app": "notepad",
                "text_length": len(message),
            },
        }

    return error_handler.wrap_automation(
        func=_write,
        operation_name="Notepad Write Text",
        context={"app": "notepad"},
    )


# =====================================================
# Tool Class for Registry Integration
# =====================================================

class AppLauncherTool(BaseTool):
    name = "app.open"
    description = "Open desktop application (Chrome, Notepad, Calculator)"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, app_name: str):
        """Open application by name"""
        return open_app(app_name)


class NotepadWriteTool(BaseTool):
    name = "notepad.write"
    description = "Open Notepad and write the provided text"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, text: str):
        return open_notepad_and_write(text)
