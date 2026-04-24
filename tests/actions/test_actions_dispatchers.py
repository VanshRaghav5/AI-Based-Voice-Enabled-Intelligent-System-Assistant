from __future__ import annotations

import importlib


def _load_action(module_name: str):
    return importlib.import_module(f"OMINI_ASSISTANT_AI.actions.{module_name}")


def test_browser_control_routes_go_to(monkeypatch):
    mod = _load_action("browser_control")

    class FakeSession:
        def go_to(self, url):
            return f"go_to:{url}"

        def run(self, value):
            return value

    class FakeRegistry:
        def get(self, _browser):
            return FakeSession()

    monkeypatch.setattr(mod, "_registry", FakeRegistry())
    monkeypatch.setattr(mod, "_log", lambda *_args, **_kwargs: None)

    result = mod.browser_control({"action": "go_to", "url": "https://example.com"})
    assert result == "go_to:https://example.com"


def test_code_helper_dispatches_write(monkeypatch):
    mod = _load_action("code_helper")

    monkeypatch.setattr(mod, "_write_action", lambda *_a, **_k: "WRITE_OK")

    result = mod.code_helper({"action": "write", "description": "hello", "language": "python", "output_path": "x.py"})
    assert result == "WRITE_OK"


def test_computer_control_dispatches_type(monkeypatch):
    mod = _load_action("computer_control")

    monkeypatch.setattr(mod, "_type", lambda text: f"typed:{text}")
    result = mod.computer_control({"action": "type", "text": "hello"})
    assert result == "typed:hello"


def test_computer_settings_requires_confirmation_for_restart(monkeypatch):
    mod = _load_action("computer_settings")

    monkeypatch.setattr(mod, "_PYAUTOGUI", True)
    result = mod.computer_settings({"action": "restart"})
    assert "Please confirm" in result


def test_desktop_control_organize(monkeypatch):
    mod = _load_action("desktop")

    monkeypatch.setattr(mod, "organize_desktop", lambda mode: f"organized:{mode}")
    result = mod.desktop_control({"action": "organize", "mode": "by_date"})
    assert result == "organized:by_date"


def test_dev_agent_calls_build_project(monkeypatch):
    mod = _load_action("dev_agent")

    monkeypatch.setattr(mod, "_build_project", lambda **kwargs: f"built:{kwargs['language']}")
    result = mod.dev_agent({"description": "build api", "language": "python"})
    assert result == "built:python"


def test_file_controller_write_and_read(tmp_path):
    mod = _load_action("file_controller")

    write_result = mod.file_controller(
        {
            "action": "write",
            "path": str(tmp_path),
            "name": "note.txt",
            "content": "hello",
        }
    )
    assert "Written to" in write_result

    read_result = mod.file_controller(
        {
            "action": "read",
            "path": str(tmp_path),
            "name": "note.txt",
        }
    )
    assert read_result == "hello"


def test_flight_finder_success(monkeypatch):
    mod = _load_action("flight_finder")

    monkeypatch.setattr(mod, "_parse_date", lambda d: "2026-05-01")
    monkeypatch.setattr(mod, "_search_flights_browser", lambda *args: ("raw", "https://google.com/travel"))
    monkeypatch.setattr(mod, "_parse_flights_with_gemini", lambda *args: [{"airline": "X", "departure": "10:00", "arrival": "12:00", "stops": 0, "price": "100", "currency": "USD"}])
    monkeypatch.setattr(mod, "_format_spoken", lambda *args: "spoken")

    result = mod.flight_finder({"origin": "IST", "destination": "LHR", "date": "tomorrow"})
    assert result == "spoken"


def test_game_updater_schedule(monkeypatch):
    mod = _load_action("game_updater")

    monkeypatch.setattr(mod, "_schedule_daily_update", lambda hour, minute: f"scheduled:{hour}:{minute}")
    result = mod.game_updater({"action": "schedule", "hour": 4, "minute": 30})
    assert result == "scheduled:4:30"


def test_open_app_no_name_returns_message():
    mod = _load_action("open_app")

    result = mod.open_app({"app_name": ""})
    assert result == "No application name provided."


def test_reminder_rejects_past_date():
    mod = _load_action("reminder")

    result = mod.reminder({"date": "2000-01-01", "time": "10:00", "message": "x"})
    assert "can't set a reminder in the past" in result


def test_screen_process_happy_path(monkeypatch):
    mod = _load_action("screen_processor")

    called = {"analyze": False}

    class FakeSession:
        def analyze(self, *_args, **_kwargs):
            called["analyze"] = True

    monkeypatch.setattr(mod, "_ensure_session", lambda **_kwargs: None)
    monkeypatch.setattr(mod, "_capture_screen", lambda: (b"img", "image/png"))
    monkeypatch.setattr(mod, "_session", FakeSession())

    result = mod.screen_process({"text": "what is on screen?", "angle": "screen"})
    assert result is True
    assert called["analyze"]


def test_send_message_validation():
    mod = _load_action("send_message")

    result = mod.send_message({"platform": "whatsapp", "receiver": "", "message_text": "hello"})
    assert result == "Please specify a recipient."


def test_weather_report_opens_browser(monkeypatch):
    mod = _load_action("weather_report")

    monkeypatch.setattr(mod.webbrowser, "open", lambda _url: True)
    result = mod.weather_action({"city": "London", "time": "today"})
    assert "Showing the weather for London" in result


def test_web_search_compare_mode(monkeypatch):
    mod = _load_action("web_search")

    monkeypatch.setattr(mod, "_compare", lambda items, aspect: f"compared:{len(items)}:{aspect}")
    result = mod.web_search({"mode": "compare", "items": ["A", "B"], "aspect": "price"})
    assert result == "compared:2:price"


def test_youtube_video_unknown_action():
    mod = _load_action("youtube_video")

    result = mod.youtube_video({"action": "something_else"})
    assert "Unknown YouTube action" in result
