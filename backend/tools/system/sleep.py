# backend/automation/system/sleep.py

import os
from backend.tools.base_tool import BaseTool
from backend.tools.error_handler import error_handler, AutomationError
from backend.utils.logger import logger


class SystemSleepTool(BaseTool):
    name = "system.sleep"
    description = "Put system to sleep mode"
    risk_level = "medium"
    requires_confirmation = True

    def execute(self):
        """Put system to sleep with error handling"""
        
        def _sleep():
            logger.warning("Putting system to sleep")
            
            try:
                # Windows command for sleep
                result = os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                
                if result != 0:
                    raise AutomationError(
                        f"Sleep command failed with code {result}",
                        "Failed to put system to sleep. You may need administrator privileges."
                    )
                
                return {
                    "status": "success",
                    "message": "System going to sleep",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"System sleep failed: {e}")
                raise AutomationError(
                    str(e),
                    "I couldn't put the system to sleep. Administrator privileges may be required."
                )
        
        return error_handler.wrap_automation(
            func=_sleep,
            operation_name="System Sleep",
            context={"operation": "sleep"}
        )


class SystemHibernateTool(BaseTool):
    name = "system.hibernate"
    description = "Hibernate the system"
    risk_level = "medium"
    requires_confirmation = True

    def execute(self):
        """Hibernate system with error handling"""
        
        def _hibernate():
            logger.warning("Hibernating system")
            
            try:
                # Windows command for hibernate
                result = os.system("shutdown /h")
                
                if result != 0:
                    raise AutomationError(
                        f"Hibernate command failed with code {result}",
                        "Failed to hibernate. Hibernate may be disabled on this system."
                    )
                
                return {
                    "status": "success",
                    "message": "System hibernating",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"System hibernate failed: {e}")
                raise AutomationError(
                    str(e),
                    "I couldn't hibernate the system. Check if hibernate is enabled in Power Options."
                )
        
        return error_handler.wrap_automation(
            func=_hibernate,
            operation_name="System Hibernate",
            context={"operation": "hibernate"}
        )
