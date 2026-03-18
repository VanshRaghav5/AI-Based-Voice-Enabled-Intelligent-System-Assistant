# backend/automation/registry_tools.py

from backend.automation.whatsapp_desktop import WhatsAppSendTool, WhatsAppOpenTool, WhatsAppOpenChatTool
from backend.automation.email_tool import EmailSendTool

from backend.automation.app_launcher import AppLauncherTool, NotepadWriteTool

from backend.automation.browser_control import (
    BrowserOpenURLTool,
    BrowserSearchGoogleTool,
    BrowserOpenYouTubeTool,
    BrowserOpenYouTubeLatestVideoTool,
)

from backend.automation.system.volume import (
    VolumeUpTool,
    VolumeDownTool,
    VolumeMuteTool
)

from backend.automation.system.power import (
    SystemLockTool,
    SystemShutdownTool,
    SystemRestartTool
)

from backend.automation.system.screenshot import (
    ScreenshotTool,
    ScreenshotRegionTool
)

from backend.automation.system.clipboard import (
    ClipboardCopyTool,
    ClipboardPasteTool,
    ClipboardClearTool
)

from backend.automation.system.window_manager import (
    MinimizeAllWindowsTool,
    MaximizeWindowTool,
    MinimizeWindowTool,
    SwitchWindowTool,
    TaskViewTool
)

from backend.automation.system.display import (
    BrightnessIncreaseTool,
    BrightnessDecreaseTool,
    BrightnessSetTool,
    MonitorOffTool
)

from backend.automation.system.sleep import (
    SystemSleepTool,
    SystemHibernateTool
)

from backend.automation.system.shortcuts import (
    OpenTaskManagerTool,
    OpenFileExplorerTool,
    OpenSettingsTool,
    OpenRunDialogTool,
    EmptyRecycleBinTool
)

from backend.automation.file.file_operations import (
    FileOpenTool,
    FileCreateTool,
    FileDeleteTool,
    FileMoveTool
)

from backend.automation.file.folder_operations import (
    FolderCreateTool,
    FolderDeleteTool
)

from backend.automation.file.file_search import FileSearchTool


def register_all_tools(registry):
    # Communication Tools
    registry.register(WhatsAppSendTool())
    registry.register(WhatsAppOpenTool())
    registry.register(WhatsAppOpenChatTool())
    registry.register(EmailSendTool())

    # App Launcher
    registry.register(AppLauncherTool())
    registry.register(NotepadWriteTool())

    # Browser Tools
    registry.register(BrowserOpenURLTool())
    registry.register(BrowserSearchGoogleTool())
    registry.register(BrowserOpenYouTubeTool())
    registry.register(BrowserOpenYouTubeLatestVideoTool())

    # Volume Control
    registry.register(VolumeUpTool())
    registry.register(VolumeDownTool())
    registry.register(VolumeMuteTool())
    
    # Power Management
    registry.register(SystemLockTool())
    registry.register(SystemShutdownTool())
    registry.register(SystemRestartTool())
    registry.register(SystemSleepTool())
    registry.register(SystemHibernateTool())

    # Screenshot Tools
    registry.register(ScreenshotTool())
    registry.register(ScreenshotRegionTool())

    # Clipboard Tools
    registry.register(ClipboardCopyTool())
    registry.register(ClipboardPasteTool())
    registry.register(ClipboardClearTool())

    # Window Management
    registry.register(MinimizeAllWindowsTool())
    registry.register(MaximizeWindowTool())
    registry.register(MinimizeWindowTool())
    registry.register(SwitchWindowTool())
    registry.register(TaskViewTool())

    # Display Control
    registry.register(BrightnessIncreaseTool())
    registry.register(BrightnessDecreaseTool())
    registry.register(BrightnessSetTool())
    registry.register(MonitorOffTool())

    # System Shortcuts
    registry.register(OpenTaskManagerTool())
    registry.register(OpenFileExplorerTool())
    registry.register(OpenSettingsTool())
    registry.register(OpenRunDialogTool())
    registry.register(EmptyRecycleBinTool())

    # File Operations
    registry.register(FileOpenTool())
    registry.register(FileCreateTool())
    registry.register(FileDeleteTool())
    registry.register(FileMoveTool())

    # Folder Operations
    registry.register(FolderCreateTool())
    registry.register(FolderDeleteTool())

    # File Search
    registry.register(FileSearchTool())
