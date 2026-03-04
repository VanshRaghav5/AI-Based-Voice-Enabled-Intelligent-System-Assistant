# backend/automation/system/display.py

import subprocess
import screen_brightness_control as sbc
from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


class BrightnessIncreaseTool(BaseTool):
    name = "display.brightness.increase"
    description = "Increase screen brightness"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, step: int = 10):
        """Increase brightness with error handling"""
        
        def _brightness_up():
            logger.info(f"Increasing brightness by {step}%")
            
            try:
                # Validate step
                if step < 1 or step > 100:
                    raise ValueError("Brightness step must be between 1 and 100")
                
                # Get current brightness
                current = sbc.get_brightness(display=0)[0]
                new_brightness = min(100, current + step)
                
                # Set new brightness
                sbc.set_brightness(new_brightness, display=0)
                
                logger.info(f"Brightness set to {new_brightness}%")
                
                return {
                    "status": "success",
                    "message": f"Brightness increased to {new_brightness}%",
                    "data": {"brightness": new_brightness, "previous": current}
                }
                
            except Exception as e:
                logger.error(f"Brightness increase failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to increase brightness. Your display may not support software brightness control."
                )
        
        return error_handler.wrap_automation(
            func=_brightness_up,
            operation_name="Increase Brightness",
            context={"operation": "brightness_up", "step": step}
        )


class BrightnessDecreaseTool(BaseTool):
    name = "display.brightness.decrease"
    description = "Decrease screen brightness"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, step: int = 10):
        """Decrease brightness with error handling"""
        
        def _brightness_down():
            logger.info(f"Decreasing brightness by {step}%")
            
            try:
                # Validate step
                if step < 1 or step > 100:
                    raise ValueError("Brightness step must be between 1 and 100")
                
                # Get current brightness
                current = sbc.get_brightness(display=0)[0]
                new_brightness = max(0, current - step)
                
                # Set new brightness
                sbc.set_brightness(new_brightness, display=0)
                
                logger.info(f"Brightness set to {new_brightness}%")
                
                return {
                    "status": "success",
                    "message": f"Brightness decreased to {new_brightness}%",
                    "data": {"brightness": new_brightness, "previous": current}
                }
                
            except Exception as e:
                logger.error(f"Brightness decrease failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to decrease brightness. Your display may not support software brightness control."
                )
        
        return error_handler.wrap_automation(
            func=_brightness_down,
            operation_name="Decrease Brightness",
            context={"operation": "brightness_down", "step": step}
        )


class BrightnessSetTool(BaseTool):
    name = "display.brightness.set"
    description = "Set screen brightness to specific level"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, level: int):
        """Set brightness to specific level with error handling"""
        
        def _brightness_set():
            logger.info(f"Setting brightness to {level}%")
            
            try:
                # Validate level
                if level < 0 or level > 100:
                    raise ValueError("Brightness level must be between 0 and 100")
                
                # Get current brightness for logging
                current = sbc.get_brightness(display=0)[0]
                
                # Set new brightness
                sbc.set_brightness(level, display=0)
                
                logger.info(f"Brightness set to {level}%")
                
                return {
                    "status": "success",
                    "message": f"Brightness set to {level}%",
                    "data": {"brightness": level, "previous": current}
                }
                
            except Exception as e:
                logger.error(f"Brightness set failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to set brightness. Your display may not support software brightness control."
                )
        
        return error_handler.wrap_automation(
            func=_brightness_set,
            operation_name="Set Brightness",
            context={"operation": "brightness_set", "level": level}
        )


class MonitorOffTool(BaseTool):
    name = "display.monitor.off"
    description = "Turn off monitor/display"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Turn off monitor with error handling"""
        
        def _monitor_off():
            logger.info("Turning off monitor")
            
            try:
                # Use Windows command to turn off monitor
                # This sends a power save signal to the display
                import ctypes
                ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
                
                return {
                    "status": "success",
                    "message": "Monitor turned off",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Monitor off failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to turn off monitor. Move your mouse to turn it back on."
                )
        
        return error_handler.wrap_automation(
            func=_monitor_off,
            operation_name="Turn Off Monitor",
            context={"operation": "monitor_off"}
        )
