# backend/automation/window_detection.py

import ctypes
import time
from typing import Optional, List
from backend.utils.logger import logger

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import psutil
except ImportError:
    psutil = None


class WindowDetector:
    """Utility for detecting and verifying window states before automation"""
    
    @staticmethod
    def is_window_active(window_title_part: str, timeout: int = 5) -> bool:
        """
        Check if a window with matching title is active/exists
        
        Args:
            window_title_part: Part of the window title to search for
            timeout: Maximum seconds to wait for window
            
        Returns:
            True if window found, False otherwise
        """
        try:
            if gw is None:
                logger.warning("pygetwindow not available, skipping window detection")
                return True
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                windows = gw.getAllTitles()
                for title in windows:
                    if window_title_part.lower() in title.lower():
                        logger.info(f"Window detected: {title}")
                        return True
                time.sleep(0.5)
            
            logger.warning(f"Window not found: {window_title_part} (timeout after {timeout}s)")
            return False
            
        except Exception as e:
            logger.error(f"Window detection error: {e}")
            return False
    
    @staticmethod
    def wait_for_window(window_title_part: str, timeout: int = 10) -> bool:
        """
        Wait for a window to appear
        
        Args:
            window_title_part: Part of the window title to search for
            timeout: Maximum seconds to wait
            
        Returns:
            True if window appeared, False if timeout
        """
        return WindowDetector.is_window_active(window_title_part, timeout)
    
    @staticmethod
    def focus_window(window_title_part: str) -> bool:
        """
        Bring a window to foreground
        
        Args:
            window_title_part: Part of the window title to search for
            
        Returns:
            True if window focused successfully
        """
        try:
            if gw is None:
                logger.warning("pygetwindow not available, skipping window focus")
                return True
            
            windows = gw.getWindowsWithTitle(window_title_part)
            if not windows:
                logger.warning(f"Could not find window to focus: {window_title_part}")
                return False

            window = windows[0]

            try:
                if getattr(window, "isMinimized", False):
                    window.restore()
                    time.sleep(0.25)

                window.activate()
                time.sleep(0.40)
            except Exception as activate_error:
                err_text = str(activate_error).lower()

                # Windows/pygetwindow can throw this noisy false-negative even when
                # the window is present and focused. Treat as soft failure.
                if "error code from windows: 0" in err_text:
                    logger.warning(
                        "Window activate reported Windows code 0; treating as soft focus failure and continuing"
                    )
                    return WindowDetector.is_window_active(window_title_part, timeout=1)

                logger.error(f"Window focus error: {activate_error}")
                return False

            try:
                active = gw.getActiveWindow()
                active_title = getattr(active, "title", "") if active else ""
            except Exception:
                active_title = ""

            if active_title and window_title_part.lower() in active_title.lower():
                logger.info(f"Focused window: {active_title}")
                return True

            # Some environments block active-window introspection; if the target
            # window exists after activation, continue optimistically.
            if WindowDetector.is_window_active(window_title_part, timeout=1):
                logger.info(f"Focused window (presence-verified): {window.title}")
                return True

            logger.warning(f"Window focus verification failed: {window_title_part}")
            return False
                
        except Exception as e:
            logger.error(f"Window focus error: {e}")
            return False
    
    @staticmethod
    def is_process_running(process_name: str) -> bool:
        """
        Check if a process is currently running
        
        Args:
            process_name: Name of the process (e.g., 'WhatsApp.exe')
            
        Returns:
            True if process is running
        """
        try:
            if psutil is None:
                logger.warning("psutil not available, skipping process detection")
                return True
            
            process_name_lower = process_name.lower()
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == process_name_lower:
                        logger.debug(f"Process found: {process_name}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.debug(f"Process not found: {process_name}")
            return False
            
        except Exception as e:
            logger.error(f"Process detection error: {e}")
            return False
    
    @staticmethod
    def wait_for_process(process_name: str, timeout: int = 10) -> bool:
        """
        Wait for a process to start
        
        Args:
            process_name: Name of the process
            timeout: Maximum seconds to wait
            
        Returns:
            True if process started, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if WindowDetector.is_process_running(process_name):
                return True
            time.sleep(0.5)
        
        logger.warning(f"Process did not start within timeout: {process_name}")
        return False


# Convenience instance
window_detector = WindowDetector()
