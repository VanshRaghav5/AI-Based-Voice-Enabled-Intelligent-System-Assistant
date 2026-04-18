# backend/automation/system/screenshot.py

import os
import uuid
from datetime import datetime
from PIL import ImageGrab
from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


class ScreenshotTool(BaseTool):
    name = "system.screenshot"
    description = "Take a screenshot and save to Desktop"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, filename: str = None):
        """Take screenshot with error handling"""
        
        def _screenshot():
            logger.info("Taking screenshot")
            
            try:
                # Capture the screen
                screenshot = ImageGrab.grab()
                
                # Generate filename if not provided
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    default_filename = f"screenshot_{timestamp}.png"
                else:
                    # Ensure .png extension
                    if not filename.lower().endswith('.png'):
                        default_filename = f"{filename}.png"
                    else:
                        default_filename = filename
                
                # Save to Desktop
                desktop = os.path.join(os.path.expanduser("~"), "Desktop"); os.makedirs(desktop, exist_ok=True)
                filepath = os.path.join(desktop, default_filename)
                
                screenshot.save(filepath, "PNG")
                
                logger.info(f"Screenshot saved to: {filepath}")
                
                return {
                    "status": "success",
                    "message": f"Screenshot saved as {default_filename}",
                    "data": {"path": filepath}
                }
                
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to take screenshot. Please check your permissions."
                )
        
        return error_handler.wrap_automation(
            func=_screenshot,
            operation_name="Screenshot",
            context={"operation": "screenshot"}
        )


class ScreenshotRegionTool(BaseTool):
    name = "system.screenshot.region"
    description = "Take a screenshot of a specific region"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, x: int, y: int, width: int, height: int, filename: str = None):
        """Take region screenshot with error handling"""
        
        def _screenshot_region():
            logger.info(f"Taking screenshot of region ({x}, {y}, {width}, {height})")
            
            try:
                # Capture the specified region
                bbox = (x, y, x + width, y + height)
                screenshot = ImageGrab.grab(bbox=bbox)
                
                # Generate filename if not provided
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    default_filename = f"screenshot_region_{timestamp}.png"
                else:
                    if not filename.lower().endswith('.png'):
                        default_filename = f"{filename}.png"
                    else:
                        default_filename = filename
                
                # Save to Desktop
                desktop = os.path.join(os.path.expanduser("~"), "Desktop"); os.makedirs(desktop, exist_ok=True)
                filepath = os.path.join(desktop, default_filename)
                
                screenshot.save(filepath, "PNG")
                
                logger.info(f"Region screenshot saved to: {filepath}")
                
                return {
                    "status": "success",
                    "message": f"Region screenshot saved as {default_filename}",
                    "data": {"path": filepath, "region": bbox}
                }
                
            except Exception as e:
                logger.error(f"Region screenshot failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to take region screenshot. Please check your coordinates."
                )
        
        return error_handler.wrap_automation(
            func=_screenshot_region,
            operation_name="Screenshot Region",
            context={"operation": "screenshot_region", "region": (x, y, width, height)}
        )
