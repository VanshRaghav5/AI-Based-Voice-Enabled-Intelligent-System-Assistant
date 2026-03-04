# backend/automation/system/shortcuts.py

import pyautogui
from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


class OpenTaskManagerTool(BaseTool):
    name = "system.task_manager"
    description = "Open Windows Task Manager"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Open Task Manager with error handling"""
        
        def _task_manager():
            logger.info("Opening Task Manager")
            
            try:
                # Ctrl+Shift+Esc
                pyautogui.hotkey('ctrl', 'shift', 'esc')
                
                return {
                    "status": "success",
                    "message": "Task Manager opened",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Task Manager open failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to open Task Manager. Try pressing Ctrl+Shift+Esc manually."
                )
        
        return error_handler.wrap_automation(
            func=_task_manager,
            operation_name="Open Task Manager",
            context={"operation": "task_manager"}
        )


class OpenFileExplorerTool(BaseTool):
    name = "system.file_explorer"
    description = "Open Windows File Explorer"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Open File Explorer with error handling"""
        
        def _file_explorer():
            logger.info("Opening File Explorer")
            
            try:
                # Windows+E
                pyautogui.hotkey('win', 'e')
                
                return {
                    "status": "success",
                    "message": "File Explorer opened",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"File Explorer open failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to open File Explorer. Try pressing Windows+E manually."
                )
        
        return error_handler.wrap_automation(
            func=_file_explorer,
            operation_name="Open File Explorer",
            context={"operation": "file_explorer"}
        )


class OpenSettingsTool(BaseTool):
    name = "system.settings"
    description = "Open Windows Settings"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Open Windows Settings with error handling"""
        
        def _settings():
            logger.info("Opening Windows Settings")
            
            try:
                # Windows+I
                pyautogui.hotkey('win', 'i')
                
                return {
                    "status": "success",
                    "message": "Windows Settings opened",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Settings open failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to open Settings. Try pressing Windows+I manually."
                )
        
        return error_handler.wrap_automation(
            func=_settings,
            operation_name="Open Windows Settings",
            context={"operation": "settings"}
        )


class OpenRunDialogTool(BaseTool):
    name = "system.run_dialog"
    description = "Open Windows Run dialog"
    risk_level = "low"
    requires_confirmation = False

    def execute(self):
        """Open Run dialog with error handling"""
        
        def _run_dialog():
            logger.info("Opening Run dialog")
            
            try:
                # Windows+R
                pyautogui.hotkey('win', 'r')
                
                return {
                    "status": "success",
                    "message": "Run dialog opened",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Run dialog open failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to open Run dialog. Try pressing Windows+R manually."
                )
        
        return error_handler.wrap_automation(
            func=_run_dialog,
            operation_name="Open Run Dialog",
            context={"operation": "run_dialog"}
        )


class EmptyRecycleBinTool(BaseTool):
    name = "system.recycle_bin.empty"
    description = "Empty the Recycle Bin"
    risk_level = "high"
    requires_confirmation = True

    def execute(self):
        """Empty Recycle Bin with error handling"""
        
        def _empty_recycle():
            logger.warning("Emptying Recycle Bin")
            
            try:
                import winshell
                winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
                
                return {
                    "status": "success",
                    "message": "Recycle Bin emptied",
                    "data": {}
                }
                
            except Exception as e:
                logger.error(f"Empty Recycle Bin failed: {e}")
                raise AutomationError(
                    str(e),
                    "Failed to empty Recycle Bin. You may need administrator privileges."
                )
        
        return error_handler.wrap_automation(
            func=_empty_recycle,
            operation_name="Empty Recycle Bin",
            context={"operation": "empty_recycle_bin"}
        )
