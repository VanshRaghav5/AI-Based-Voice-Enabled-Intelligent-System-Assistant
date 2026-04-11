# backend/automation/system/power.py

import ctypes
import os
from backend.tools.base_tool import BaseTool
from backend.tools.error_handler import error_handler, AutomationError
from backend.utils.logger import logger


class SystemLockTool(BaseTool):
    name = "system.lock"
    description = "Lock Windows system"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Lock Windows system with error handling"""
        
        def _lock():
            logger.info("Attempting to lock system")
            
            try:
                result = ctypes.windll.user32.LockWorkStation()
                
                if result == 0:
                    raise AutomationError(
                        "LockWorkStation returned 0",
                        "Failed to lock the system. Please try pressing Windows+L manually."
                    )
                
                return {
                    "status": "success",
                    "message": "System locked successfully",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"System lock failed: {e}")
                raise AutomationError(
                    str(e),
                    "I couldn't lock the system. Try pressing Windows+L on your keyboard."
                )
        
        return error_handler.wrap_automation(
            func=_lock,
            operation_name="Lock System",
            context={"operation": "lock"}
        )


class SystemShutdownTool(BaseTool):
    name = "system.shutdown"
    description = "Shutdown the computer"
    risk_level = "high"
    requires_confirmation = True

    def execute(self):
        """Shutdown system with error handling"""
        
        def _shutdown():
            logger.warning("Initiating system shutdown via tool")
            
            try:
                result = os.system("shutdown /s /t 0")
                
                if result != 0:
                    raise AutomationError(
                        f"Shutdown command failed with code {result}",
                        "Failed to shutdown. You may need administrator privileges."
                    )
                
                return {
                    "status": "success",
                    "message": "Shutting down system now",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Shutdown failed: {e}")
                raise AutomationError(
                    str(e),
                    "I couldn't shutdown the system. Administrator privileges may be required."
                )
        
        return error_handler.wrap_automation(
            func=_shutdown,
            operation_name="System Shutdown",
            context={"operation": "shutdown"}
        )


class SystemRestartTool(BaseTool):
    name = "system.restart"
    description = "Restart the computer"
    risk_level = "high"
    requires_confirmation = True

    def execute(self):
        """Restart system with error handling"""
        
        def _restart():
            logger.warning("Initiating system restart via tool")
            
            try:
                result = os.system("shutdown /r /t 0")
                
                if result != 0:
                    raise AutomationError(
                        f"Restart command failed with code {result}",
                        "Failed to restart. You may need administrator privileges."
                    )
                
                return {
                    "status": "success",
                    "message": "Restarting system now",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Restart failed: {e}")
                raise AutomationError(
                    str(e),
                    "I couldn't restart the system. Administrator privileges may be required."
                )
        
        return error_handler.wrap_automation(
            func=_restart,
            operation_name="System Restart",
            context={"operation": "restart"}
        )
