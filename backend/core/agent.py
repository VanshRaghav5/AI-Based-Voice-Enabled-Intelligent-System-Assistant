# backend/core/agent.py

import re
from backend.core.tool_call import ToolCall
from backend.config.logger import logger


class Agent:

    def decide(self, text: str) -> ToolCall:
        logger.info(f"[Agent] Deciding tool for: {text}")

        text = text.strip()
        text_lower = text.lower()

        # Remove control characters
        text_lower = re.sub(r"[^\x20-\x7E]", "", text_lower)

        # -------------------------
        # SYSTEM VOLUME
        # -------------------------
        if "volume up" in text_lower:
            return ToolCall("system.volume.up", {})

        if "volume down" in text_lower:
            return ToolCall("system.volume.down", {})

        if "mute" in text_lower:
            return ToolCall("system.volume.mute", {})

        # -------------------------
        # SYSTEM POWER
        # -------------------------
        if "lock" in text_lower:
            return ToolCall("system.lock", {})

        if "shutdown" in text_lower:
            return ToolCall("system.shutdown", {})

        if "restart" in text_lower:
            return ToolCall("system.restart", {})

        # -------------------------
        # WHATSAPP SEND
        # send hello to swayam
        # -------------------------
        send_pattern = r"send (.+) to (.+)"
        match = re.search(send_pattern, text_lower)

        if match:
            message = match.group(1).strip()
            target = match.group(2).strip().title()

            return ToolCall(
                "whatsapp.send",
                {
                    "target": target,
                    "message": message
                }
            )

        # -------------------------
        # FILE OPEN
        # open file C:\test.txt
        # -------------------------
        open_pattern = r"open file (.+)"
        match = re.search(open_pattern, text_lower)

        if match:
            path = match.group(1).strip()
            return ToolCall("file.open", {"path": path})

        # -------------------------
        # FILE CREATE
        # create file C:\test.txt
        # -------------------------
        create_pattern = r"create file (.+)"
        match = re.search(create_pattern, text_lower)

        if match:
            path = match.group(1).strip()
            return ToolCall("file.create", {"path": path})

        # -------------------------
        # FILE DELETE
        # delete file C:\test.txt
        # -------------------------
        delete_pattern = r"delete file (.+)"
        match = re.search(delete_pattern, text_lower)

        if match:
            path = match.group(1).strip()
            return ToolCall("file.delete", {"path": path})

        # -------------------------
        # FILE MOVE
        # move file C:\a.txt to C:\b.txt
        # -------------------------
        move_pattern = r"move file (.+) to (.+)"
        match = re.search(move_pattern, text_lower)

        if match:
            source = match.group(1).strip()
            destination = match.group(2).strip()

            return ToolCall(
                "file.move",
                {
                    "source": source,
                    "destination": destination
                }
            )

        # -------------------------
        # FOLDER CREATE
        # create folder C:\newfolder
        # -------------------------
        folder_create_pattern = r"create folder (.+)"
        match = re.search(folder_create_pattern, text_lower)

        if match:
            path = match.group(1).strip()
            return ToolCall("folder.create", {"path": path})

        # -------------------------
        # FOLDER DELETE
        # delete folder C:\newfolder
        # -------------------------
        folder_delete_pattern = r"delete folder (.+)"
        match = re.search(folder_delete_pattern, text_lower)

        if match:
            path = match.group(1).strip()
            return ToolCall("folder.delete", {"path": path})

        # -------------------------
        # FILE SEARCH
        # search file report
        # -------------------------
        search_pattern = r"search file (.+)"
        match = re.search(search_pattern, text_lower)

        if match:
            filename = match.group(1).strip()
            return ToolCall("file.search", {"filename": filename})

        # -------------------------
        # UNKNOWN
        # -------------------------
        logger.info("[Agent] No rule matched. Returning unknown.")

        return ToolCall("unknown", {})
