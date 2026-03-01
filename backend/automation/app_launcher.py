import subprocess
import os
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
