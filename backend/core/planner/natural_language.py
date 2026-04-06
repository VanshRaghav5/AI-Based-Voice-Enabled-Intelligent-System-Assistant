import re


def _parse_clock_time(time_text: str):
    """Parse user-friendly clock text to (hour, minute)."""
    cleaned = str(time_text or "").strip().lower()
    cleaned = re.sub(r"\s+", "", cleaned)

    match_12h = re.match(r"^(\d{1,2})(?::(\d{2}))?(am|pm)$", cleaned)
    if match_12h:
        hour = int(match_12h.group(1))
        minute = int(match_12h.group(2) or 0)
        meridiem = match_12h.group(3)
        if hour < 1 or hour > 12 or minute < 0 or minute > 59:
            return None
        if meridiem == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12
        return hour, minute

    match_24h = re.match(r"^(\d{1,2}):(\d{2})$", cleaned)
    if match_24h:
        hour = int(match_24h.group(1))
        minute = int(match_24h.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
        return None

    match_hour = re.match(r"^(\d{1,2})$", cleaned)
    if match_hour:
        hour = int(match_hour.group(1))
        if 0 <= hour <= 23:
            return hour, 0

    return None


def parse_natural_schedule_command(text: str):
    """Parse natural schedule commands for create/list/delete actions."""
    raw = str(text or "").strip()
    if not raw:
        return None

    cleaned = re.sub(r"\s+", " ", raw).strip()
    lowered = cleaned.lower()

    if re.match(r"^(list|show|view)\s+(my\s+)?(schedules|scheduled tasks|schedule)$", lowered):
        return {"action": "list"}
    if re.match(r"^what( are|'re)? my schedules\??$", lowered):
        return {"action": "list"}

    delete_match = re.match(r"^(delete|remove|cancel)\s+schedule\s+(\d+)$", lowered)
    if delete_match:
        return {"action": "delete", "task_id": int(delete_match.group(2))}

    daily_match = re.match(r"^schedule\s+(.+?)\s+(every day|daily)\s+at\s+(.+)$", cleaned, flags=re.IGNORECASE)
    if daily_match:
        command = daily_match.group(1).strip()
        parsed_time = _parse_clock_time(daily_match.group(3).strip())
        if not parsed_time:
            return {"action": "invalid", "message": "Could not understand the schedule time."}

        hour, minute = parsed_time
        return {
            "action": "create",
            "name": f"Daily: {command[:60]}",
            "command": command,
            "trigger_type": "cron",
            "cron_expression": f"{minute} {hour} * * *",
            "description": f"every day at {hour:02d}:{minute:02d}",
        }

    interval_match = re.match(
        r"^schedule\s+(.+?)\s+every\s+(\d+)\s*(minute|minutes|min|hour|hours|hr|hrs|day|days)$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if interval_match:
        command = interval_match.group(1).strip()
        amount = int(interval_match.group(2))
        unit = interval_match.group(3).lower()

        if amount <= 0:
            return {"action": "invalid", "message": "Interval must be greater than zero."}

        multiplier = 60
        normalized_unit = "minute"
        if unit in {"hour", "hours", "hr", "hrs"}:
            multiplier = 3600
            normalized_unit = "hour"
        elif unit in {"day", "days"}:
            multiplier = 86400
            normalized_unit = "day"

        interval_seconds = amount * multiplier
        unit_label = normalized_unit if amount == 1 else f"{normalized_unit}s"

        return {
            "action": "create",
            "name": f"Recurring: {command[:60]}",
            "command": command,
            "trigger_type": "interval",
            "interval_seconds": interval_seconds,
            "description": f"every {amount} {unit_label}",
        }

    return None