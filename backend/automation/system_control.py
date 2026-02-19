import os
import subprocess


def shutdown_system(confirm: bool = False) -> dict:
    """
    Shutdown the system.
    Requires confirm=True for safety.
    """
    if not confirm:
        return {
            "status": "error",
            "message": "Shutdown not confirmed."
        }

    try:
        os.system("shutdown /s /t 5")
        return {
            "status": "success",
            "message": "System will shutdown in 5 seconds."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def restart_system(confirm: bool = False) -> dict:
    """
    Restart the system.
    Requires confirm=True for safety.
    """
    if not confirm:
        return {
            "status": "error",
            "message": "Restart not confirmed."
        }

    try:
        os.system("shutdown /r /t 5")
        return {
            "status": "success",
            "message": "System will restart in 5 seconds."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def lock_system() -> dict:
    """
    Lock Windows system.
    """
    try:
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation")
        return {
            "status": "success",
            "message": "System locked."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
