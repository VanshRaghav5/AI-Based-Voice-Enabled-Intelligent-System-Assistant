# backend/automation/system/datetime_tools.py

from datetime import datetime
from typing import Dict, Any

from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler


class CurrentTimeTool(BaseTool):
    name = "system.time"
    description = "Get the current operating system time"
    risk_level = "low"
    requires_confirmation = False

    def execute(self) -> Dict[str, Any]:
        def _get_time():
            now = datetime.now()
            # e.g. "It is currently 10:30 AM"
            time_str = now.strftime("%I:%M %p")
            return {
                "status": "success",
                "message": f"It is currently {time_str}.",
                "data": {"time": time_str, "timestamp": now.timestamp()},
            }

        return error_handler.wrap_automation(
            func=_get_time,
            operation_name="Current Time",
            context={},
        )


class CurrentDateTool(BaseTool):
    name = "system.date"
    description = "Get the current operating system date and day of the week"
    risk_level = "low"
    requires_confirmation = False

    def execute(self) -> Dict[str, Any]:
        def _get_date():
            now = datetime.now()
            # e.g. "Today is Monday, October 23rd, 2023"
            
            # Add proper suffix to the day
            day = now.day
            if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][day % 10 - 1]

            day_str = now.strftime(f"%A, %B {day}{suffix}, %Y")
            
            return {
                "status": "success",
                "message": f"Today is {day_str}.",
                "data": {"date": day_str, "timestamp": now.timestamp()},
            }

        return error_handler.wrap_automation(
            func=_get_date,
            operation_name="Current Date",
            context={},
        )
