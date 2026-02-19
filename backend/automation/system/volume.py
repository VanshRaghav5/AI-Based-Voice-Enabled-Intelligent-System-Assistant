# backend/automation/system/volume.py

import ctypes
from backend.automation.base_tool import BaseTool


class VolumeUpTool(BaseTool):
    name = "system.volume.up"
    description = "Increase system volume"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, step: int = 5):
        try:
            for _ in range(step):
                ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)

            return {
                "status": "success",
                "message": "Volume increased",
                "data": {}
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }


class VolumeDownTool(BaseTool):
    name = "system.volume.down"
    description = "Decrease system volume"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, step: int = 5):
        try:
            for _ in range(step):
                ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)

            return {
                "status": "success",
                "message": "Volume decreased",
                "data": {}
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }


class VolumeMuteTool(BaseTool):
    name = "system.volume.mute"
    description = "Mute or unmute system volume"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        try:
            ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)

            return {
                "status": "success",
                "message": "Volume toggled",
                "data": {}
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }
