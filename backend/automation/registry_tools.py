# backend/automation/registry_tools.py

from backend.automation.whatsapp_desktop import WhatsAppSendTool

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
    registry.register(WhatsAppSendTool())

    registry.register(VolumeUpTool())
    registry.register(VolumeDownTool())
    registry.register(VolumeMuteTool())
    registry.register(SystemLockTool())
    registry.register(SystemShutdownTool())
    registry.register(SystemRestartTool())

    registry.register(FileOpenTool())
    registry.register(FileCreateTool())
    registry.register(FileDeleteTool())
    registry.register(FileMoveTool())

    registry.register(FolderCreateTool())
    registry.register(FolderDeleteTool())

    registry.register(FileSearchTool())
