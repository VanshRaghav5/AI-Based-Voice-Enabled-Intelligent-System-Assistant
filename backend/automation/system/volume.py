# backend/automation/system/volume.py

import ctypes
from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


class VolumeUpTool(BaseTool):
    name = "system.volume.up"
    description = "Increase system volume"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, step: int = 5):
        """Increase volume with error handling"""
        
        def _volume_up():
            logger.info(f"Increasing volume by {step} steps")
            
            try:
                # Validate step parameter
                if step < 1 or step > 50:
                    raise ValueError("Volume step must be between 1 and 50")
                
                for _ in range(step):
                    try:
                        ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
                    except Exception as e:
                        logger.error(f"Failed to send volume up key: {e}")
                        raise AutomationError(
                            str(e),
                            "Failed to increase volume. Please try using your keyboard volume keys."
                        )

                return {
                    "status": "success",
                    "message": f"Volume increased by {step} steps",
                    "data": {"steps": step}
                }
                
            except ValueError as e:
                logger.error(f"Invalid volume step: {e}")
                raise
            except Exception as e:
                logger.error(f"Volume up failed: {e}")
                raise AutomationError(
                    str(e),
                    "Couldn't increase volume. Try using your volume keys."
                )
        
        return error_handler.wrap_automation(
            func=_volume_up,
            operation_name="Volume Up",
            context={"operation": "volume_up", "step": step}
        )


class VolumeDownTool(BaseTool):
    name = "system.volume.down"
    description = "Decrease system volume"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, step: int = 5):
        """Decrease volume with error handling"""
        
        def _volume_down():
            logger.info(f"Decreasing volume by {step} steps")
            
            try:
                # Validate step parameter
                if step < 1 or step > 50:
                    raise ValueError("Volume step must be between 1 and 50")
                
                for _ in range(step):
                    try:
                        ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
                    except Exception as e:
                        logger.error(f"Failed to send volume down key: {e}")
                        raise AutomationError(
                            str(e),
                            "Failed to decrease volume. Please try using your keyboard volume keys."
                        )

                return {
                    "status": "success",
                    "message": f"Volume decreased by {step} steps",
                    "data": {"steps": step}
                }
                
            except ValueError as e:
                logger.error(f"Invalid volume step: {e}")
                raise
            except Exception as e:
                logger.error(f"Volume down failed: {e}")
                raise AutomationError(
                    str(e),
                    "Couldn't decrease volume. Try using your volume keys."
                )
        
        return error_handler.wrap_automation(
            func=_volume_down,
            operation_name="Volume Down",
            context={"operation": "volume_down", "step": step}
        )


class VolumeMuteTool(BaseTool):
    name = "system.volume.mute"
    description = "Mute or unmute system volume"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Toggle mute with error handling"""
        
        def _volume_mute():
            logger.info("Toggling volume mute")
            
            try:
                ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)

                return {
                    "status": "success",
                    "message": "Volume mute toggled",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Volume mute toggle failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to toggle mute. Try using your keyboard mute button."
                )
        
        return error_handler.wrap_automation(
            func=_volume_mute,
            operation_name="Volume Mute Toggle",
            context={"operation": "volume_mute"}
        )
