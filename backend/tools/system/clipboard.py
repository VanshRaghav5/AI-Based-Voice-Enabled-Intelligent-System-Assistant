# backend/automation/system/clipboard.py

import pyperclip
from backend.tools.base_tool import BaseTool
from backend.tools.error_handler import error_handler, AutomationError
from backend.utils.logger import logger


class ClipboardCopyTool(BaseTool):
    name = "clipboard.copy"
    description = "Copy text to clipboard"
    risk_level = "low"
    requires_confirmation = False

    def execute(self, text: str):
        """Copy text to clipboard with error handling"""
        
        def _copy():
            if not text:
                raise ValueError("Text cannot be empty")
            
            logger.info(f"Copying to clipboard: {text[:50]}...")
            
            try:
                pyperclip.copy(text)
                
                return {
                    "status": "success",
                    "message": f"Copied {len(text)} characters to clipboard",
                    "data": {"text_length": len(text)}
                }
                
            except Exception as e:
                logger.error(f"Clipboard copy failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to copy to clipboard. Please try again."
                )
        
        return error_handler.wrap_automation(
            func=_copy,
            operation_name="Clipboard Copy",
            context={"operation": "clipboard_copy"}
        )


class ClipboardPasteTool(BaseTool):
    name = "clipboard.paste"
    description = "Get text from clipboard"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Get clipboard content with error handling"""
        
        def _paste():
            logger.info("Reading from clipboard")
            
            try:
                text = pyperclip.paste()
                
                if not text:
                    return {
                        "status": "success",
                        "message": "Clipboard is empty",
                        "data": {"text": ""}
                    }
                
                return {
                    "status": "success",
                    "message": f"Retrieved {len(text)} characters from clipboard",
                    "data": {"text": text, "text_length": len(text)}
                }
                
            except Exception as e:
                logger.error(f"Clipboard paste failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to read from clipboard. Please try again."
                )
        
        return error_handler.wrap_automation(
            func=_paste,
            operation_name="Clipboard Paste",
            context={"operation": "clipboard_paste"}
        )


class ClipboardClearTool(BaseTool):
    name = "clipboard.clear"
    description = "Clear clipboard content"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Clear clipboard with error handling"""
        
        def _clear():
            logger.info("Clearing clipboard")
            
            try:
                pyperclip.copy("")
                
                return {
                    "status": "success",
                    "message": "Clipboard cleared",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Clipboard clear failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to clear clipboard. Please try again."
                )
        
        return error_handler.wrap_automation(
            func=_clear,
            operation_name="Clipboard Clear",
            context={"operation": "clipboard_clear"}
        )
