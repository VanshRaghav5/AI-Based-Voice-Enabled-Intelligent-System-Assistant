# backend/automation/system/power.py

import ctypes
import os
from backend.automation.base_tool import BaseTool


class SystemLockTool(BaseTool):
    name = "system.lock"
    description = "Lock Windows system"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        try:
            ctypes.windll.user32.LockWorkStation()

            return {
                "status": "success",
                "message": "System locked",
                "data": {}
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }


class SystemShutdownTool(BaseTool):
    name = "system.shutdown"
    description = "Shutdown the computer"
    risk_level = "high"
    requires_confirmation = True

    def execute(self):
        try:
            os.system("shutdown /s /t 0")

            return {
                "status": "success",
                "message": "Shutting down system",
                "data": {}
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }


class SystemRestartTool(BaseTool):
    name = "system.restart"
    description = "Restart the computer"
    risk_level = "high"
    requires_confirmation = True

    def execute(self):
        try:
            os.system("shutdown /r /t 0")

            return {
                "status": "success",
                "message": "Restarting system",
                "data": {}
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }
