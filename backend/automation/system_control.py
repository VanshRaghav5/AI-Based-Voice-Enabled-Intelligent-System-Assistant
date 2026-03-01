import os
import subprocess
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


def shutdown_system(confirm: bool = False) -> dict:
    """
    Shutdown the system with comprehensive error handling.
    Requires confirm=True for safety.
    """
    if not confirm:
        logger.warning("Shutdown attempt without confirmation")
        return {
            "status": "error",
            "message": "Shutdown requires confirmation for safety.",
            "data": {}
        }

    def _shutdown():
        logger.warning("Initiating system shutdown")
        
        try:
            result = os.system("shutdown /s /t 5")
            
            if result != 0:
                raise AutomationError(
                    f"Shutdown command failed with code {result}",
                    "Failed to shutdown the system. You may need administrator privileges."
                )
            
            return {
                "status": "success",
                "message": "System will shutdown in 5 seconds",
                "data": {"delay": 5}
            }
            
        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
            raise AutomationError(
                str(e),
                "I couldn't shutdown the system. You may need administrator privileges."
            )
    
    return error_handler.wrap_automation(
        func=_shutdown,
        operation_name="System Shutdown",
        context={"operation": "shutdown"}
    )


def restart_system(confirm: bool = False) -> dict:
    """
    Restart the system with comprehensive error handling.
    Requires confirm=True for safety.
    """
    if not confirm:
        logger.warning("Restart attempt without confirmation")
        return {
            "status": "error",
            "message": "Restart requires confirmation for safety.",
            "data": {}
        }

    def _restart():
        logger.warning("Initiating system restart")
        
        try:
            result = os.system("shutdown /r /t 5")
            
            if result != 0:
                raise AutomationError(
                    f"Restart command failed with code {result}",
                    "Failed to restart the system. You may need administrator privileges."
                )
            
            return {
                "status": "success",
                "message": "System will restart in 5 seconds",
                "data": {"delay": 5}
            }
            
        except Exception as e:
            logger.error(f"Restart failed: {e}")
            raise AutomationError(
                str(e),
                "I couldn't restart the system. You may need administrator privileges."
            )
    
    return error_handler.wrap_automation(
        func=_restart,
        operation_name="System Restart",
        context={"operation": "restart"}
    )


def lock_system() -> dict:
    """
    Lock Windows system with error handling.
    """
    
    def _lock():
        logger.info("Locking system")
        
        try:
            result = subprocess.Popen("rundll32.exe user32.dll,LockWorkStation")
            
            # Give it a moment to execute
            import time
            time.sleep(0.5)
            
            return {
                "status": "success",
                "message": "System locked",
                "data": {}
            }
            
        except Exception as e:
            logger.error(f"Lock system failed: {e}")
            raise AutomationError(
                str(e),
                "I couldn't lock the system. Please try locking it manually with Windows+L."
            )
    
    return error_handler.wrap_automation(
        func=_lock,
        operation_name="Lock System",
        context={"operation": "lock"}
    )
