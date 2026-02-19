from backend.core.tool_call import ToolCall
from backend.core.tool_registry import ToolRegistry
from backend.automation.whatsapp_desktop import WhatsAppSendTool

registry = ToolRegistry()
registry.register(WhatsAppSendTool())

call = ToolCall(
    name="whatsapp.send",
    args={"target": "Swayam", "message": "Test"}
)

print(registry.execute(call))
