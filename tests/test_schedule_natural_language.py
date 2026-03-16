import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


from backend.scheduling.natural_language import parse_natural_schedule_command


def test_parse_schedule_interval_command():
    intent = parse_natural_schedule_command("schedule open youtube every 2 hours")

    assert intent is not None
    assert intent["action"] == "create"
    assert intent["trigger_type"] == "interval"
    assert intent["interval_seconds"] == 7200
    assert intent["command"] == "open youtube"


def test_parse_schedule_daily_command():
    intent = parse_natural_schedule_command("schedule open notepad daily at 9:30 pm")

    assert intent is not None
    assert intent["action"] == "create"
    assert intent["trigger_type"] == "cron"
    assert intent["cron_expression"] == "30 21 * * *"


def test_parse_schedule_list_command():
    intent = parse_natural_schedule_command("show my scheduled tasks")
    assert intent == {"action": "list"}


def test_parse_schedule_delete_command():
    intent = parse_natural_schedule_command("cancel schedule 12")
    assert intent == {"action": "delete", "task_id": 12}


def test_parse_schedule_invalid_time_command():
    intent = parse_natural_schedule_command("schedule open calculator every day at 25:99")

    assert intent is not None
    assert intent["action"] == "invalid"