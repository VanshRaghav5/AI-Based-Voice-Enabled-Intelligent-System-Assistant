import subprocess
import os


APP_MAP = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe"
}


def open_app(app_name: str) -> dict:
    """
    Opens a desktop application.
    Returns structured response.
    """

    app_name = app_name.lower()

    if app_name not in APP_MAP:
        return {
            "status": "error",
            "message": f"Application '{app_name}' not found."
        }

    try:
        subprocess.Popen(APP_MAP[app_name], shell=True)

        return {
            "status": "success",
            "message": f"Opening {app_name}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
