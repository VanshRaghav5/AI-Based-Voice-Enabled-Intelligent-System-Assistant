import asyncio
import inspect
import re
import threading
import json
import sys
import traceback
from pathlib import Path

import sounddevice as sd
from google import genai
from google.genai import types
from security import (
    check_api_rate_limit, check_tool_rate_limit, check_file_write_limit,
    check_code_execution_limit, sanitize_path_input, validate_path_input,
    validate_filename_input, sanitize_text_input, SecurityLogger,
    authorize_tool, authenticate_user, get_auth_manager
)
from ui import OminiUI
from voice.offline_bridge import OfflineVoiceBridge
from memory.memory_manager import (
    load_memory, update_memory, format_memory_for_prompt,
)

from actions.flight_finder     import flight_finder
from actions.open_app          import open_app
from actions.weather_report    import weather_action
from actions.send_message      import send_message
from actions.reminder          import reminder
from actions.computer_settings import computer_settings
from actions.screen_processor  import screen_process
from actions.youtube_video     import youtube_video
from actions.desktop           import desktop_control
from actions.browser_control   import browser_control
from actions.file_controller   import file_controller
from actions.code_helper       import code_helper
from actions.dev_agent         import dev_agent
from actions.web_search        import web_search as web_search_action
from actions.computer_control  import computer_control
from actions.game_updater      import game_updater
from actions.system_control_agent import system_control_agent
from actions.file_intelligence_agent import file_intelligence_agent
from agent.app_state_agent import app_state_agent
from agent.system_state_monitor import get_system_state_monitor
from agent.background_scheduler import get_background_scheduler
from agent.event_automation_engine import get_event_automation_engine
from core.event_bus import get_event_bus
from core.activity_logger import get_activity_logger
from core.activity_replay import ActivityReplay
from core.safety_layer import get_safety_layer
from core.persona_manager import get_persona_manager
from core.voice_manager import get_voice_manager, get_live_voice_manager


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"
LIVE_MODEL          = "models/gemini-2.5-flash-native-audio-preview-12-2025"
CHANNELS            = 1
SEND_SAMPLE_RATE    = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE          = 1024


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are OMINI, Tony Stark's AI assistant. "
            "Be concise, direct, and always use the provided tools to complete tasks. "
            "Never simulate or guess results — always call the appropriate tool."
        )


def _build_persona_prompt() -> str:
    try:
        return get_persona_manager().build_prompt_suffix()
    except Exception:
        return (
            "\n[PERSONA: Executive]\n"
            "Fast, precise, and outcome-driven.\n"
            "Response rules:\n"
            "- Lead with the answer.\n"
            "- Keep replies compact.\n"
            "- Avoid filler.\n"
            "Always stay direct, smooth, and clean."
        )


# ── Transkripsiyon temizleyici ─────────────────────────────────────────────────
_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)

def _clean_transcript(text: str) -> str:
    """Gemini'nin ürettiği <ctrlXX> artefaktlarını ve kontrol karakterlerini temizler."""
    text = _CTRL_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()


# ── Tool declarations ──────────────────────────────────────────────────────────
TOOL_DECLARATIONS = [
    {
        "name": "open_app",
        "description": (
            "Opens any application on the computer. "
            "Use this whenever the user asks to open, launch, or start any app, "
            "website, or program. Always call this tool — never just say you opened it."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "app_name": {
                    "type": "STRING",
                    "description": "Exact name of the application (e.g. 'WhatsApp', 'Chrome', 'Spotify')"
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "web_search",
        "description": "Searches the web for any information.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query":  {"type": "STRING", "description": "Search query"},
                "mode":   {"type": "STRING", "description": "search (default) or compare"},
                "items":  {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Items to compare"},
                "aspect": {"type": "STRING", "description": "price | specs | reviews"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "weather_report",
        "description": "Gives the weather report to user",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "city": {"type": "STRING", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "send_message",
        "description": "Sends a text message via WhatsApp, Telegram, or other messaging platform.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "receiver":     {"type": "STRING", "description": "Recipient contact name"},
                "message_text": {"type": "STRING", "description": "The message to send"},
                "platform":     {"type": "STRING", "description": "Platform: WhatsApp, Telegram, etc."}
            },
            "required": ["receiver", "message_text", "platform"]
        }
    },
    {
        "name": "reminder",
        "description": "Sets a timed reminder using Task Scheduler.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "date":    {"type": "STRING", "description": "Date in YYYY-MM-DD format"},
                "time":    {"type": "STRING", "description": "Time in HH:MM format (24h)"},
                "message": {"type": "STRING", "description": "Reminder message text"}
            },
            "required": ["date", "time", "message"]
        }
    },
    {
        "name": "youtube_video",
        "description": (
            "Controls YouTube. Use for: playing videos, summarizing a video's content, "
            "getting video info, or showing trending videos."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "play | summarize | get_info | trending (default: play)"},
                "query":  {"type": "STRING", "description": "Search query for play action"},
                "save":   {"type": "BOOLEAN", "description": "Save summary to Notepad (summarize only)"},
                "region": {"type": "STRING", "description": "Country code for trending e.g. TR, US"},
                "url":    {"type": "STRING", "description": "Video URL for get_info action"},
            },
            "required": []
        }
    },
    {
        "name": "screen_process",
        "description": (
            "Captures and analyzes the screen or webcam image. "
            "MUST be called when user asks what is on screen, what you see, "
            "analyze my screen, look at camera, etc. "
            "You have NO visual ability without this tool. "
            "After calling this tool, stay SILENT — the vision module speaks directly."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "angle": {"type": "STRING", "description": "'screen' to capture display, 'camera' for webcam. Default: 'screen'"},
                "text":  {"type": "STRING", "description": "The question or instruction about the captured image"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "computer_settings",
        "description": (
            "Controls the computer: volume, brightness, window management, keyboard shortcuts, "
            "typing text on screen, closing apps, fullscreen, dark mode, WiFi, restart, shutdown, "
            "scrolling, tab management, zoom, screenshots, lock screen, refresh/reload page. "
            "Use for ANY single computer control command. NEVER route to agent_task."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "The action to perform"},
                "description": {"type": "STRING", "description": "Natural language description of what to do"},
                "value":       {"type": "STRING", "description": "Optional value: volume level, text to type, etc."}
            },
            "required": []
        }
    },
    {
        "name": "browser_control",
        "description": (
            "Controls any web browser. Use for: opening websites, searching the web, "
            "clicking elements, filling forms, scrolling, screenshots, navigation, any web-based task. "
            "Always pass the 'browser' parameter when the user specifies a browser (e.g. 'open in Edge', "
            "'use Firefox', 'open Chrome'). Multiple browsers can run simultaneously."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "go_to | search | click | type | scroll | fill_form | smart_click | smart_type | get_text | get_url | press | new_tab | close_tab | screenshot | back | forward | reload | switch | list_browsers | close | close_all"},
                "browser":     {"type": "STRING", "description": "Target browser: chrome | edge | firefox | opera | operagx | brave | vivaldi | safari. Omit to use the currently active browser."},
                "url":         {"type": "STRING", "description": "URL for go_to / new_tab action"},
                "query":       {"type": "STRING", "description": "Search query for search action"},
                "engine":      {"type": "STRING", "description": "Search engine: google | bing | duckduckgo | yandex (default: google)"},
                "selector":    {"type": "STRING", "description": "CSS selector for click/type"},
                "text":        {"type": "STRING", "description": "Text to click or type"},
                "description": {"type": "STRING", "description": "Element description for smart_click/smart_type"},
                "direction":   {"type": "STRING", "description": "up | down for scroll"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount in pixels (default: 500)"},
                "key":         {"type": "STRING", "description": "Key name for press action (e.g. Enter, Escape, F5)"},
                "path":        {"type": "STRING", "description": "Save path for screenshot"},
                "incognito":   {"type": "BOOLEAN", "description": "Open in private/incognito mode"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_controller",
        "description": "Manages files and folders: list, create, delete, move, copy, rename, read, write, find, disk usage.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "list | create_file | create_folder | delete | move | copy | rename | read | write | find | largest | disk_usage | organize_desktop | info"},
                "path":        {"type": "STRING", "description": "File/folder path or shortcut: desktop, downloads, documents, home"},
                "destination": {"type": "STRING", "description": "Destination path for move/copy"},
                "new_name":    {"type": "STRING", "description": "New name for rename"},
                "content":     {"type": "STRING", "description": "Content for create_file/write"},
                "name":        {"type": "STRING", "description": "File name to search for"},
                "extension":   {"type": "STRING", "description": "File extension to search (e.g. .pdf)"},
                "count":       {"type": "INTEGER", "description": "Number of results for largest"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "desktop_control",
        "description": "Controls the desktop: wallpaper, organize, clean, list, stats.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "wallpaper | wallpaper_url | organize | clean | list | stats | task"},
                "path":   {"type": "STRING", "description": "Image path for wallpaper"},
                "url":    {"type": "STRING", "description": "Image URL for wallpaper_url"},
                "mode":   {"type": "STRING", "description": "by_type or by_date for organize"},
                "task":   {"type": "STRING", "description": "Natural language desktop task"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "code_helper",
        "description": "Writes, edits, explains, runs, or builds code files.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "write | edit | explain | run | build | auto (default: auto)"},
                "description": {"type": "STRING", "description": "What the code should do or what change to make"},
                "language":    {"type": "STRING", "description": "Programming language (default: python)"},
                "output_path": {"type": "STRING", "description": "Where to save the file"},
                "file_path":   {"type": "STRING", "description": "Path to existing file for edit/explain/run/build"},
                "code":        {"type": "STRING", "description": "Raw code string for explain"},
                "args":        {"type": "STRING", "description": "CLI arguments for run/build"},
                "timeout":     {"type": "INTEGER", "description": "Execution timeout in seconds (default: 30)"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "dev_agent",
        "description": "Builds complete multi-file projects from scratch: plans, writes files, installs deps, opens VSCode, runs and fixes errors.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "description":  {"type": "STRING", "description": "What the project should do"},
                "language":     {"type": "STRING", "description": "Programming language (default: python)"},
                "project_name": {"type": "STRING", "description": "Optional project folder name"},
                "timeout":      {"type": "INTEGER", "description": "Run timeout in seconds (default: 30)"},
            },
            "required": ["description"]
        }
    },
    {
        "name": "agent_task",
        "description": (
            "Executes complex multi-step tasks requiring multiple different tools. "
            "Examples: 'research X and save to file', 'find and organize files'. "
            "DO NOT use for single commands. NEVER use for Steam/Epic — use game_updater."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal":     {"type": "STRING", "description": "Complete description of what to accomplish"},
                "priority": {"type": "STRING", "description": "low | normal | high (default: normal)"}
            },
            "required": ["goal"]
        }
    },
    {
        "name": "computer_control",
        "description": "Direct computer control: type, click, hotkeys, scroll, move mouse, screenshots, find elements on screen.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":      {"type": "STRING", "description": "type | smart_type | click | double_click | right_click | hotkey | press | scroll | move | copy | paste | screenshot | wait | clear_field | focus_window | screen_find | screen_click | random_data | user_data"},
                "text":        {"type": "STRING", "description": "Text to type or paste"},
                "x":           {"type": "INTEGER", "description": "X coordinate"},
                "y":           {"type": "INTEGER", "description": "Y coordinate"},
                "keys":        {"type": "STRING", "description": "Key combination e.g. 'ctrl+c'"},
                "key":         {"type": "STRING", "description": "Single key e.g. 'enter'"},
                "direction":   {"type": "STRING", "description": "up | down | left | right"},
                "amount":      {"type": "INTEGER", "description": "Scroll amount (default: 3)"},
                "seconds":     {"type": "NUMBER",  "description": "Seconds to wait"},
                "title":       {"type": "STRING",  "description": "Window title for focus_window"},
                "description": {"type": "STRING",  "description": "Element description for screen_find/screen_click"},
                "type":        {"type": "STRING",  "description": "Data type for random_data"},
                "field":       {"type": "STRING",  "description": "Field for user_data: name|email|city"},
                "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing (default: true)"},
                "path":        {"type": "STRING",  "description": "Save path for screenshot"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "game_updater",
        "description": (
            "THE ONLY tool for ANY Steam or Epic Games request. "
            "Use for: installing, downloading, updating games, listing installed games, "
            "checking download status, scheduling updates. "
            "ALWAYS call directly for any Steam/Epic/game request. "
            "NEVER use agent_task, browser_control, or web_search for Steam/Epic."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action":    {"type": "STRING",  "description": "update | install | list | download_status | schedule | cancel_schedule | schedule_status (default: update)"},
                "platform":  {"type": "STRING",  "description": "steam | epic | both (default: both)"},
                "game_name": {"type": "STRING",  "description": "Game name (partial match supported)"},
                "app_id":    {"type": "STRING",  "description": "Steam AppID for install (optional)"},
                "hour":      {"type": "INTEGER", "description": "Hour for scheduled update 0-23 (default: 3)"},
                "minute":    {"type": "INTEGER", "description": "Minute for scheduled update 0-59 (default: 0)"},
                "shutdown_when_done": {"type": "BOOLEAN", "description": "Shut down PC when download finishes"},
            },
            "required": []
        }
    },
    {
        "name": "flight_finder",
        "description": "Searches Google Flights and speaks the best options.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "origin":      {"type": "STRING",  "description": "Departure city or airport code"},
                "destination": {"type": "STRING",  "description": "Arrival city or airport code"},
                "date":        {"type": "STRING",  "description": "Departure date (any format)"},
                "return_date": {"type": "STRING",  "description": "Return date for round trips"},
                "passengers":  {"type": "INTEGER", "description": "Number of passengers (default: 1)"},
                "cabin":       {"type": "STRING",  "description": "economy | premium | business | first"},
                "save":        {"type": "BOOLEAN", "description": "Save results to Notepad"},
            },
            "required": ["origin", "destination", "date"]
        }
    },
    {
        "name": "system_control_agent",
        "description": (
            "Safe OS control layer for lock, shutdown, restart, sleep and process management. "
            "Dangerous actions require confirmation_token from a previous prompt."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "lock | shutdown | shutdown_in | restart | restart_in | sleep | kill_process | list_processes"},
                "minutes": {"type": "INTEGER", "description": "Delay in minutes for shutdown_in/restart_in"},
                "process_name": {"type": "STRING", "description": "Target process executable name, e.g. chrome.exe"},
                "pid": {"type": "INTEGER", "description": "Target process id"},
                "limit": {"type": "INTEGER", "description": "Max process rows for list_processes"},
                "confirmation_token": {"type": "STRING", "description": "Token returned by safety layer for risky actions"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "system_monitor_agent",
        "description": "Controls and queries background system monitor (CPU/RAM/process/battery/thermal alerts).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "start | stop | status | snapshot"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "file_intelligence_agent",
        "description": "Advanced file intelligence: large files, duplicates, temp/cache cleanup, disk trend snapshots.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "find_large_files | find_duplicates | clean_temp_cache | disk_trend"},
                "path": {"type": "STRING", "description": "Target path shortcut or absolute path"},
                "min_size_gb": {"type": "NUMBER", "description": "Minimum file size in GB"},
                "limit": {"type": "INTEGER", "description": "Maximum results"},
                "limit_groups": {"type": "INTEGER", "description": "Maximum duplicate groups"},
                "confirmation_token": {"type": "STRING", "description": "Token returned by safety layer for risky actions"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "app_automation_agent",
        "description": "Context-aware app automation with state checks before action execution.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "send_whatsapp_message | check_app_state"},
                "app_name": {"type": "STRING", "description": "Application name for state checks"},
                "receiver": {"type": "STRING", "description": "Recipient for send actions"},
                "message_text": {"type": "STRING", "description": "Message body"},
                "confirmation_token": {"type": "STRING", "description": "Token returned by safety layer for risky actions"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "scheduler_agent",
        "description": "Background recurring scheduler for periodic assistant jobs.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "schedule | schedule_defaults | cancel | list"},
                "name": {"type": "STRING", "description": "Job name"},
                "interval_seconds": {"type": "INTEGER", "description": "Recurring interval in seconds"},
                "job_action": {"type": "STRING", "description": "Job action such as drink_water_reminder or temp_cleanup_reminder"},
                "payload": {"type": "OBJECT", "description": "Job payload"},
                "job_id": {"type": "STRING", "description": "Job id for cancel"},
            },
            "required": ["action"]
        }
    },
    {
        "name": "activity_replay",
        "description": "Audit and replay helper for activity logs.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "recent | replay_hint | replay_last_safe"},
                "limit": {"type": "INTEGER", "description": "Maximum rows"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "shutdown_omini",
        "description": (
            "Shuts down the assistant completely. "
            "Call this when the user expresses intent to end the conversation, "
            "close the assistant, say goodbye, or stop Omini. "
            "The user can say this in ANY language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        }
    },
    {
        "name": "auth_login",
        "description": (
            "Login to unlock restricted tools. "
            "Call this with username and password to authenticate. "
            "After login, use auth_logout when done."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "username": {"type": "STRING", "description": "Username"},
                "password": {"type": "STRING", "description": "Password"},
            },
            "required": ["username", "password"]
        }
    },
    {
        "name": "auth_logout",
        "description": "Logout to lock restricted tools.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        }
    },
    {
        "name": "auth_status",
        "description": "Check current authentication status.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        }
    },
    {
        "name": "save_memory",
        "description": (
            "Save an important personal fact about the user to long-term memory. "
            "Call this silently whenever the user reveals something worth remembering: "
            "name, age, city, job, preferences, hobbies, relationships, projects, or future plans. "
            "Do NOT call for: weather, reminders, searches, or one-time commands. "
            "Do NOT announce that you are saving — just call it silently. "
            "Values must be in English regardless of the conversation language."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": (
                        "identity — name, age, birthday, city, job, language, nationality | "
                        "preferences — favorite food/color/music/film/game/sport, hobbies | "
                        "projects — active projects, goals, things being built | "
                        "relationships — friends, family, partner, colleagues | "
                        "wishes — future plans, things to buy, travel dreams | "
                        "notes — habits, schedule, anything else worth remembering"
                    )
                },
                "key":   {"type": "STRING", "description": "Short snake_case key (e.g. name, favorite_food, sister_name)"},
                "value": {"type": "STRING", "description": "Concise value in English (e.g. Fatih, pizza, older sister)"},
            },
            "required": ["category", "key", "value"]
        }
    },
]


class OminiLive:

    def __init__(self, ui: OminiUI):
        self.ui             = ui
        self.session        = None
        self.audio_in_queue = None
        self.out_queue      = None
        self._loop          = None
        self._is_speaking   = False
        self._speaking_lock = threading.Lock()
        self.ui.on_text_command = self._on_text_command
        self._turn_done_event: asyncio.Event | None = None
        self._queued_offline_turns: list[str] = []
        self._offline_voice = OfflineVoiceBridge(BASE_DIR)
        self._offline_mode_announced = False
        self._live_reconnect_requested = False
        self._offline_system_prompt = (
            self._build_offline_system_prompt()
        )
        self._offline_allowed_tools = {
            "open_app",
            "computer_settings",
            "file_controller",
            "desktop_control",
            "computer_control",
            "reminder",
            "shutdown_omini",
        }
        self._event_bus = get_event_bus()
        self._activity_logger = get_activity_logger(BASE_DIR)
        self._activity_replay = ActivityReplay(BASE_DIR)
        self._safety = get_safety_layer()
        self._persona_manager = get_persona_manager()
        self._persona_key = self._persona_manager.get_selected_key()
        self._voice_manager = get_voice_manager()
        self._live_voice_manager = get_live_voice_manager()
        self._live_voice_key = self._live_voice_manager.get_selected_key()
        self._monitor = get_system_state_monitor()
        self._scheduler = get_background_scheduler()
        self._event_engine = get_event_automation_engine()

        self._monitor.start()
        self._scheduler.start()
        self._event_engine.start()
        self._event_bus.subscribe("assistant.suggestion", self._on_assistant_suggestion)
        self._event_bus.subscribe("scheduler.job_due", self._on_scheduler_job_due)
        self.ui.persona_changed.connect(self._on_persona_changed)
        self.ui.voice_changed.connect(self._on_voice_changed)
        self.ui.live_voice_changed.connect(self._on_live_voice_changed)

        try:
            self._offline_voice.set_voice_key(self._voice_manager.get_selected_key())
        except Exception:
            pass

        # Baseline recurring jobs: hydration reminder every 2h and daily temp cleanup reminder.
        self._scheduler.schedule(
            name="hydration_every_2h",
            interval_seconds=7200,
            action="drink_water_reminder",
            payload={"message": "Hydration reminder: drink water."},
        )
        self._scheduler.schedule(
            name="temp_cleanup_daily",
            interval_seconds=86400,
            action="temp_cleanup",
            payload={"message": "Daily temp cleanup executed."},
        )

    def _build_offline_system_prompt(self) -> str:
        return (
            "You are OMINI running in offline fallback mode. "
            "Be concise, practical, and transparent about offline limitations. "
            "If a task requires internet, say so briefly and suggest the next best local action."
            f"{_build_persona_prompt()}"
        )

    def _get_live_voice_name(self) -> str:
        key = self._live_voice_key or self._live_voice_manager.get_selected_key()
        profile = self._live_voice_manager.get_selected_profile()
        if profile.key != key:
            profile = self._live_voice_manager.set_selected_key(key)
        return profile.key

    @staticmethod
    def _is_live_voice_error(error: Exception) -> bool:
        text = str(error).lower()
        return any(
            phrase in text
            for phrase in (
                "voice",
                "prebuiltvoiceconfig",
                "prebuilt voice",
                "invalid argument",
                "unsupported",
                "unknown field",
            )
        )

    def _request_live_reconnect(self) -> None:
        self._live_reconnect_requested = True
        session = self.session
        loop = self._loop
        if not session or not loop:
            return

        close_method = getattr(session, "close", None)
        if not callable(close_method):
            return

        try:
            result = close_method()
            if inspect.isawaitable(result):
                asyncio.run_coroutine_threadsafe(result, loop)
        except Exception:
            pass

    def _on_persona_changed(self, persona_key: str):
        self._persona_key = persona_key or self._persona_manager.get_selected_key()
        self._offline_system_prompt = self._build_offline_system_prompt()
        self.ui.write_log(f"SYS: Persona updated to {self._persona_key}. Applies on the next live session reconnect.")

    def _on_voice_changed(self, voice_key: str):
        try:
            if self._offline_voice.set_voice_key(voice_key):
                self.ui.write_log(f"SYS: Voice updated to {voice_key}.")
            else:
                self.ui.write_log("SYS: Voice update failed; keeping the current voice.")
        except Exception:
            self.ui.write_log("SYS: Voice update failed; keeping the current voice.")

    def _on_live_voice_changed(self, live_voice_key: str):
        self._live_voice_key = live_voice_key or self._live_voice_manager.get_selected_key()
        self.ui.write_log(f"SYS: Gemini voice updated to {self._live_voice_key}. Reconnecting now.")
        self._request_live_reconnect()

    def _on_assistant_suggestion(self, event: dict):
        payload = event.get("payload", {})
        message = str(payload.get("message", "")).strip()
        if message:
            self.ui.write_log(f"SYS SUGGESTION: {message}")
            if not self.ui.muted:
                self._offline_voice.speak(message)

    def _on_scheduler_job_due(self, event: dict):
        payload = event.get("payload", {})
        action = str(payload.get("action", "")).strip().lower()
        data = payload.get("payload", {}) or {}

        if action == "temp_cleanup":
            result = file_intelligence_agent(
                parameters={"action": "clean_temp_cache"},
                player=self.ui,
            )
            self.ui.write_log(f"SYS SCHEDULER: {result}")
        elif action == "disk_trend_snapshot":
            result = file_intelligence_agent(
                parameters={"action": "disk_trend", "path": data.get("path", "home")},
                player=self.ui,
            )
            self.ui.write_log(f"SYS SCHEDULER: {result}")

    def _on_text_command(self, text: str):
        clean = (text or "").strip()
        if not clean:
            return

        if not self._loop or not self.session:
            if self._offline_voice.has_internet():
                self._queue_offline_turn(clean)
            else:
                threading.Thread(
                    target=self._respond_with_offline_llm,
                    args=(clean,),
                    daemon=True,
                ).start()
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": clean}]},
                turn_complete=True
            ),
            self._loop
        )

    def _queue_offline_turn(self, text: str):
        self._queued_offline_turns.append(text)
        self.ui.write_log("SYS: Saved command for retry when internet is back.")
        self._offline_voice.speak("Saved. I will run this when internet is back.")

    def _execute_offline_tool(self, tool_name: str, args: dict) -> str:
        result = "Done."
        try:
            if tool_name == "open_app":
                r = open_app(parameters=args, response=None, player=self.ui)
                result = r or f"Opened {args.get('app_name', 'app')}."
            elif tool_name == "computer_settings":
                r = computer_settings(parameters=args, response=None, player=self.ui)
                result = r or "Computer settings updated."
            elif tool_name == "file_controller":
                r = file_controller(parameters=args, player=self.ui)
                result = r or "File operation completed."
            elif tool_name == "desktop_control":
                r = desktop_control(parameters=args, player=self.ui)
                result = r or "Desktop task completed."
            elif tool_name == "computer_control":
                r = computer_control(parameters=args, player=self.ui)
                result = r or "Computer action completed."
            elif tool_name == "reminder":
                r = reminder(parameters=args, response=None, player=self.ui)
                result = r or "Reminder set."
            elif tool_name == "shutdown_omini":
                self.ui.write_log("SYS: Shutdown requested (offline mode).")
                result = "Goodbye, sir."
                def _shutdown():
                    import time, os
                    time.sleep(1)
                    os._exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()
            else:
                result = "This action is not available offline."
        except Exception as e:
            result = f"Offline tool '{tool_name}' failed: {e}"
            traceback.print_exc()
        return str(result)

    def _speak_offline_reply(self, text: str):
        clean_reply = _clean_transcript(text)
        if not clean_reply:
            return
        self.ui.write_log(f"Omini: {clean_reply}")
        self.ui.set_state("SPEAKING")
        self._offline_voice.speak(clean_reply)

    def _respond_with_offline_llm(self, user_text: str):
        self.ui.set_state("THINKING")

        plan = self._offline_voice.plan_offline_turn(
            user_text,
            allowed_tools=sorted(self._offline_allowed_tools),
            system_prompt=self._offline_system_prompt,
        )

        if plan.get("mode") == "tool":
            tool_name = str(plan.get("tool_name", "")).strip()
            args = plan.get("args", {})
            if not isinstance(args, dict):
                args = {}

            self.ui.write_log(f"SYS: Offline tool call -> {tool_name} {args}")
            tool_result = self._execute_offline_tool(tool_name, args)
            spoken = str(plan.get("reply", "")).strip() or tool_result
            self._speak_offline_reply(spoken)
        else:
            reply = str(plan.get("reply", "")).strip()
            if reply:
                self._speak_offline_reply(reply)
            else:
                self.ui.write_log("SYS: Local Ollama unavailable; command saved for online retry.")
                self._queued_offline_turns.append(user_text)

        if not self.ui.muted:
            self.ui.set_state("LISTENING")

    async def _replay_offline_turns(self):
        if not self._queued_offline_turns or not self.session:
            return

        queued = list(self._queued_offline_turns)
        self._queued_offline_turns.clear()

        self.ui.write_log(f"SYS: Replaying {len(queued)} offline command(s).")
        for text in queued:
            await self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True,
            )

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            self._is_speaking = value
        if value:
            self.ui.set_state("SPEAKING")
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")

    def speak(self, text: str):
        if not self._loop or not self.session:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns={"parts": [{"text": text}]},
                turn_complete=True
            ),
            self._loop
        )

    def speak_error(self, tool_name: str, error: str):
        short = str(error)[:120]
        self.ui.write_log(f"ERR: {tool_name} — {short}")
        self.speak(f"Sir, {tool_name} encountered an error. {short}")

    def _build_config(self) -> types.LiveConnectConfig:
        from datetime import datetime

        memory     = load_memory()
        mem_str    = format_memory_for_prompt(memory)
        sys_prompt = _load_system_prompt()

        now      = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")
        time_ctx = (
            f"[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            f"Use this to calculate exact times for reminders.\n\n"
        )

        parts = [time_ctx]
        if mem_str:
            parts.append(mem_str)
        parts.append(sys_prompt)
        parts.append(_build_persona_prompt())

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self._get_live_voice_name()
                    )
                )
            ),
        )

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})
        actor = get_auth_manager().get_current_user() or "guest"
        action_name = str(args.get("action", name)).strip().lower() or name

        # ── Authorization check for sensitive tools ───────────────────────────
        sensitive_tools = {
            "file_controller": ["write", "create_file", "delete", "move", "copy"],
            "code_helper": ["write", "edit", "run"],
            "dev_agent": None,
            "send_message": None,
            "game_updater": None,
            "system_control_agent": None,
            "file_intelligence_agent": ["clean_temp_cache"],
            "scheduler_agent": None,
            "app_automation_agent": None,
        }
        if name in sensitive_tools:
            action = args.get("action", None)
            allowed, msg = authorize_tool(name, action)
            if not allowed:
                print(f"[OMINI] 🔒 Unauthorized: {msg}")
                return types.FunctionResponse(
                    id=fc.id, name=name,
                    response={"result": msg, "error": True}
                )

        # ── Rate limiting check ───────────────────────────────────────────────
        allowed, message = check_tool_rate_limit()
        if not allowed:
            print(f"[OMINI] ⚠️ Rate limit: {message}")
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": message, "error": True}
            )

        risk = self._safety.score_risk(name, action_name, args)
        if self._safety.requires_confirmation(risk):
            token = str(args.get("confirmation_token", "")).strip()
            if token:
                ok, reason = self._safety.validate_confirmation(
                    token=token,
                    actor=actor,
                    tool=name,
                    action=action_name,
                    params={k: v for k, v in args.items() if k != "confirmation_token"},
                )
                if not ok:
                    self._activity_logger.log(
                        actor=actor,
                        action=action_name,
                        tool=name,
                        status="blocked",
                        details={"reason": reason, "risk": risk},
                    )
                    return types.FunctionResponse(
                        id=fc.id,
                        name=name,
                        response={"result": reason, "error": True},
                    )
            else:
                req = self._safety.issue_confirmation(
                    actor=actor,
                    tool=name,
                    action=action_name,
                    params={k: v for k, v in args.items() if k != "confirmation_token"},
                )
                prompt = (
                    f"Safety confirmation required ({req.risk} risk) for {name}:{action_name}. "
                    f"Call the same tool again with confirmation_token='{req.token}' within 120 seconds."
                )
                self._activity_logger.log(
                    actor=actor,
                    action=action_name,
                    tool=name,
                    status="pending_confirmation",
                    details={"risk": req.risk, "token": req.token},
                )
                return types.FunctionResponse(
                    id=fc.id,
                    name=name,
                    response={"result": prompt, "error": True},
                )

        print(f"[OMINI] 🔧 {name}  {args}")
        self.ui.set_state("THINKING")
        self._activity_logger.log(
            actor=actor,
            action=action_name,
            tool=name,
            status="started",
            details={"args": {k: v for k, v in args.items() if k != "password"}},
        )

        # ── save_memory: sessiz ve hızlı ──────────────────────────────────────
        if name == "save_memory":
            category = args.get("category", "notes")
            key      = args.get("key", "")
            value    = args.get("value", "")
            if key and value:
                update_memory({category: {key: {"value": value}}})
                print(f"[Memory] 💾 save_memory: {category}/{key} = {value}")
            if not self.ui.muted:
                self.ui.set_state("LISTENING")
            return types.FunctionResponse(
                id=fc.id, name=name,
                response={"result": "ok", "silent": True}
            )

        loop   = asyncio.get_event_loop()
        result = "Done."

        try:
            if name == "open_app":
                r = await loop.run_in_executor(None, lambda: open_app(parameters=args, response=None, player=self.ui))
                result = r or f"Opened {args.get('app_name')}."

            elif name == "weather_report":
                r = await loop.run_in_executor(None, lambda: weather_action(parameters=args, player=self.ui))
                result = r or "Weather delivered."

            elif name == "browser_control":
                r = await loop.run_in_executor(None, lambda: browser_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "file_controller":
                r = await loop.run_in_executor(None, lambda: file_controller(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "send_message":
                r = await loop.run_in_executor(None, lambda: send_message(parameters=args, response=None, player=self.ui, session_memory=None))
                result = r or f"Message sent to {args.get('receiver')}."

            elif name == "reminder":
                r = await loop.run_in_executor(None, lambda: reminder(parameters=args, response=None, player=self.ui))
                result = r or "Reminder set."

            elif name == "youtube_video":
                r = await loop.run_in_executor(None, lambda: youtube_video(parameters=args, response=None, player=self.ui))
                result = r or "Done."

            elif name == "screen_process":
                threading.Thread(
                    target=screen_process,
                    kwargs={"parameters": args, "response": None,
                            "player": self.ui, "session_memory": None},
                    daemon=True
                ).start()
                result = "Vision module activated. Stay completely silent — vision module will speak directly."

            elif name == "computer_settings":
                r = await loop.run_in_executor(None, lambda: computer_settings(parameters=args, response=None, player=self.ui))
                result = r or "Done."

            elif name == "desktop_control":
                r = await loop.run_in_executor(None, lambda: desktop_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "code_helper":
                r = await loop.run_in_executor(None, lambda: code_helper(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "dev_agent":
                r = await loop.run_in_executor(None, lambda: dev_agent(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "agent_task":
                from agent.task_queue import get_queue, TaskPriority
                priority_map = {"low": TaskPriority.LOW, "normal": TaskPriority.NORMAL, "high": TaskPriority.HIGH}
                priority = priority_map.get(args.get("priority", "normal").lower(), TaskPriority.NORMAL)
                task_id  = get_queue().submit(goal=args.get("goal", ""), priority=priority, speak=self.speak)
                result   = f"Task started (ID: {task_id})."

            elif name == "web_search":
                r = await loop.run_in_executor(None, lambda: web_search_action(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "computer_control":
                r = await loop.run_in_executor(None, lambda: computer_control(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "game_updater":
                r = await loop.run_in_executor(None, lambda: game_updater(parameters=args, player=self.ui, speak=self.speak))
                result = r or "Done."

            elif name == "flight_finder":
                r = await loop.run_in_executor(None, lambda: flight_finder(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "system_control_agent":
                r = await loop.run_in_executor(None, lambda: system_control_agent(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "file_intelligence_agent":
                r = await loop.run_in_executor(None, lambda: file_intelligence_agent(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "app_automation_agent":
                r = await loop.run_in_executor(None, lambda: app_state_agent(parameters=args, player=self.ui))
                result = r or "Done."

            elif name == "system_monitor_agent":
                act = str(args.get("action", "status")).lower().strip()
                if act == "start":
                    self._monitor.start()
                    result = "System monitor started."
                elif act == "stop":
                    self._monitor.stop()
                    result = "System monitor stopped."
                elif act == "snapshot":
                    snap = self._monitor.get_last_snapshot() or {"message": "No snapshot yet."}
                    result = json.dumps(snap)
                else:
                    result = f"System monitor is {'running' if self._monitor.is_running() else 'stopped'}."

            elif name == "scheduler_agent":
                act = str(args.get("action", "list")).lower().strip()
                if act == "schedule":
                    interval = int(args.get("interval_seconds", 7200))
                    job_id = self._scheduler.schedule(
                        name=str(args.get("name", "scheduled_job")),
                        interval_seconds=interval,
                        action=str(args.get("job_action", "drink_water_reminder")),
                        payload=args.get("payload", {}) or {},
                    )
                    result = f"Scheduled job {job_id} every {interval} seconds."
                elif act == "schedule_defaults":
                    j1 = self._scheduler.schedule(
                        name="hydration_every_2h",
                        interval_seconds=7200,
                        action="drink_water_reminder",
                        payload={"message": "Hydration reminder: drink water."},
                    )
                    j2 = self._scheduler.schedule(
                        name="temp_cleanup_daily",
                        interval_seconds=86400,
                        action="temp_cleanup",
                        payload={"message": "Daily temp cleanup executed."},
                    )
                    j3 = self._scheduler.schedule(
                        name="disk_trend_every_6h",
                        interval_seconds=21600,
                        action="disk_trend_snapshot",
                        payload={"path": "home"},
                    )
                    result = f"Default schedules installed: {j1}, {j2}, {j3}"
                elif act == "cancel":
                    job_id = str(args.get("job_id", "")).strip()
                    result = "Cancelled." if (job_id and self._scheduler.cancel(job_id)) else "Job not found."
                else:
                    result = json.dumps(self._scheduler.list_jobs())

            elif name == "activity_replay":
                act = str(args.get("action", "recent")).lower().strip()
                limit = int(args.get("limit", 20))
                if act == "recent":
                    result = json.dumps(self._activity_replay.recent(limit=limit))
                elif act == "replay_last_safe":
                    replayable = self._activity_replay.get_last_safe_replayable(limit=max(50, limit))
                    if not replayable:
                        result = "No safe replayable action found."
                    else:
                        rtool = replayable.get("tool", "")
                        rargs = replayable.get("args", {}) or {}
                        if rtool == "web_search":
                            rr = await loop.run_in_executor(None, lambda: web_search_action(parameters=rargs, player=self.ui))
                            result = f"Replayed web_search: {rr}"
                        elif rtool == "weather_report":
                            rr = await loop.run_in_executor(None, lambda: weather_action(parameters=rargs, player=self.ui))
                            result = f"Replayed weather_report: {rr}"
                        elif rtool == "browser_control":
                            rr = await loop.run_in_executor(None, lambda: browser_control(parameters=rargs, player=self.ui))
                            result = f"Replayed browser_control: {rr}"
                        elif rtool == "file_intelligence_agent":
                            rr = await loop.run_in_executor(None, lambda: file_intelligence_agent(parameters=rargs, player=self.ui))
                            result = f"Replayed file_intelligence_agent: {rr}"
                        elif rtool == "system_monitor_agent":
                            ract = str(rargs.get("action", "status")).lower().strip()
                            if ract == "start":
                                self._monitor.start()
                                rr = "System monitor started."
                            elif ract == "stop":
                                self._monitor.stop()
                                rr = "System monitor stopped."
                            elif ract == "snapshot":
                                rr = json.dumps(self._monitor.get_last_snapshot() or {"message": "No snapshot yet."})
                            else:
                                rr = f"System monitor is {'running' if self._monitor.is_running() else 'stopped'}."
                            result = f"Replayed system_monitor_agent: {rr}"
                        else:
                            result = "Last safe action uses unsupported replay tool."
                else:
                    result = self._activity_replay.suggest_replay(limit=limit)

            elif name == "shutdown_omini":
                self.ui.write_log("SYS: Shutdown requested.")
                self.speak("Goodbye, sir.")
                def _shutdown():
                    import time, os
                    time.sleep(1)
                    os._exit(0)
                threading.Thread(target=_shutdown, daemon=True).start()

            elif name == "auth_login":
                username = args.get("username", "")
                password = args.get("password", "")
                success, msg = authenticate_user(username, password)
                if success:
                    self.ui.write_log(f"SYS: Login success: {msg}")
                    self.speak(f"Login successful as {username}.")
                else:
                    self.ui.write_log(f"SYS: Login failed: {msg}")
                    result = msg
                result = msg

            elif name == "auth_logout":
                get_auth_manager().logout()
                self.ui.write_log("SYS: Logged out.")
                self.speak("Logged out. Restricted tools are now locked.")

            elif name == "auth_status":
                user = get_auth_manager().get_current_user()
                if user:
                    result = f"Logged in as: {user}"
                else:
                    result = "Not authenticated. Some tools are restricted."

            else:
                result = f"Unknown tool: {name}"

        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            traceback.print_exc()
            self.speak_error(name, e)
            self._activity_logger.log(
                actor=actor,
                action=action_name,
                tool=name,
                status="failed",
                details={"error": str(e)},
            )

        else:
            self._activity_logger.log(
                actor=actor,
                action=action_name,
                tool=name,
                status="completed",
                details={"result_preview": str(result)[:220]},
            )

        if not self.ui.muted:
            self.ui.set_state("LISTENING")

        print(f"[OMINI] 📤 {name} → {str(result)[:80]}")
        return types.FunctionResponse(
            id=fc.id, name=name,
            response={"result": result}
        )

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            if self._live_reconnect_requested:
                return
            await self.session.send_realtime_input(media=msg)

    async def _listen_audio(self):
        print("[OMINI] 🎤 Mic started")
        loop = asyncio.get_event_loop()

        def callback(indata, frames, time_info, status):
            with self._speaking_lock:
                omini_speaking = self._is_speaking
            if not omini_speaking and not self.ui.muted:
                data = indata.tobytes()
                loop.call_soon_threadsafe(
                    self.out_queue.put_nowait,
                    {"data": data, "mime_type": "audio/pcm"}
                )

        try:
            with sd.InputStream(
                samplerate=SEND_SAMPLE_RATE,
                channels=CHANNELS,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=callback,
            ):
                print("[OMINI] 🎤 Mic stream open")
                while True:
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[OMINI] ❌ Mic: {e}")
            raise

    async def _receive_audio(self):
        print("[OMINI] 👂 Recv started")
        out_buf, in_buf = [], []

        try:
            while True:
                async for response in self.session.receive():

                    if response.data:
                        if self._turn_done_event and self._turn_done_event.is_set():
                            self._turn_done_event.clear()
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.output_transcription and sc.output_transcription.text:
                            txt = _clean_transcript(sc.output_transcription.text)
                            if txt:
                                out_buf.append(txt)

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = _clean_transcript(sc.input_transcription.text)
                            if txt:
                                in_buf.append(txt)

                        if sc.turn_complete:
                            if self._turn_done_event:
                                self._turn_done_event.set()

                            full_in = " ".join(in_buf).strip()
                            if full_in:
                                self.ui.write_log(f"You: {full_in}")
                            in_buf = []

                            full_out = " ".join(out_buf).strip()
                            if full_out:
                                self.ui.write_log(f"Omini: {full_out}")
                            out_buf = []

                    if response.tool_call:
                        fn_responses = []
                        for fc in response.tool_call.function_calls:
                            print(f"[OMINI] 📞 {fc.name}")
                            fr = await self._execute_tool(fc)
                            fn_responses.append(fr)
                        await self.session.send_tool_response(
                            function_responses=fn_responses
                        )

        except Exception as e:
            print(f"[OMINI] ❌ Recv: {e}")
            traceback.print_exc()
            raise

    async def _play_audio(self):
        print("[OMINI] 🔊 Play started")

        stream = sd.RawOutputStream(
            samplerate=RECEIVE_SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=CHUNK_SIZE,
        )
        stream.start()

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        self.audio_in_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    if (
                        self._turn_done_event
                        and self._turn_done_event.is_set()
                        and self.audio_in_queue.empty()
                    ):
                        self.set_speaking(False)
                        self._turn_done_event.clear()
                    continue

                self.set_speaking(True)
                await asyncio.to_thread(stream.write, chunk)

        except Exception as e:
            print(f"[OMINI] ❌ Play: {e}")
            raise
        finally:
            self.set_speaking(False)
            stream.stop()
            stream.close()

    async def run(self):
        client = genai.Client(
            api_key=_get_api_key(),
            http_options={"api_version": "v1beta"}
        )

        while True:
            if not self._offline_voice.has_internet():
                await self._run_offline_mode()
                continue

            try:
                print("[OMINI] 🔌 Connecting...")
                self.ui.set_state("THINKING")
                self._live_reconnect_requested = False
                config = self._build_config()

                async with (
                    client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session        = session
                    self._loop          = asyncio.get_event_loop()
                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue      = asyncio.Queue(maxsize=10)
                    self._turn_done_event = asyncio.Event()

                    print("[OMINI] ✅ Connected.")
                    self._offline_mode_announced = False
                    self.ui.set_state("LISTENING")
                    self.ui.write_log("SYS: OMINI online.")
                    await self._replay_offline_turns()

                    tg.create_task(self._send_realtime())
                    tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio())
                    tg.create_task(self._play_audio())

            except Exception as e:
                print(f"[OMINI] ⚠️ {e}")
                traceback.print_exc()
                if self._live_voice_key != "Charon" and self._is_live_voice_error(e):
                    self._live_voice_key = "Charon"
                    try:
                        self._live_voice_manager.set_selected_key("Charon")
                        self.ui.write_log("SYS: Gemini voice fell back to Charon.")
                    except Exception:
                        pass
                elif self._live_voice_key != "Charon":
                    self.ui.write_log("SYS: Live reconnect failed, keeping the selected Gemini voice.")

            self.set_speaking(False)
            self.ui.set_state("THINKING")
            reconnect_delay = 0.2 if self._live_reconnect_requested else 3
            self._live_reconnect_requested = False
            print(f"[OMINI] 🔄 Reconnecting in {reconnect_delay:.1f}s...")
            await asyncio.sleep(reconnect_delay)

    async def _run_offline_mode(self):
        self.session = None
        self._loop = None
        self.set_speaking(False)

        if not self._offline_mode_announced:
            self._offline_mode_announced = True
            self.ui.set_state("PROCESSING")
            self.ui.write_log("SYS: Internet unavailable. Offline voice mode active.")
            self._offline_voice.speak("Internet is unavailable. Offline voice mode is active.")
            if self._offline_voice.ollama_available():
                self.ui.write_log("SYS: Ollama fallback online.")
                self._offline_voice.speak("Local language model is ready.")
            else:
                self.ui.write_log("SYS: Ollama not reachable; commands will be queued.")
                self._offline_voice.speak("Local model is not reachable. I will queue your commands.")

        while not self._offline_voice.has_internet():
            self.ui.set_state("LISTENING")
            text = await asyncio.to_thread(self._offline_voice.listen_and_transcribe_once)
            if text:
                clean = _clean_transcript(text)
                if clean:
                    self.ui.write_log(f"You: {clean}")
                    await asyncio.to_thread(self._respond_with_offline_llm, clean)
            await asyncio.sleep(0.2)

        self.ui.write_log("SYS: Internet restored. Returning to live mode.")
        self._offline_voice.speak("Internet is back. Returning to live mode.")
        self._offline_mode_announced = False


def main():
    # Show login screen first
    from ui import LoginScreen, OminiUI
    from security import get_auth_manager, authenticate_user
    from PySide6 import QtWidgets, QtCore

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])

    login = LoginScreen()
    login.show()

    # Use a local event loop for login only
    logged_in = [False]
    local_loop = QtCore.QEventLoop()

    def on_login(username, mode):
        logged_in[0] = True
        login.close()
        local_loop.quit()

    login.login_success.connect(on_login)
    local_loop.exec()

    if not logged_in[0]:
        return  # Exit if not logged in

    # Now start main UI
    ui = OminiUI("face.png")

    def runner():
        ui.wait_for_api_key()
        omini = OminiLive(ui)
        try:
            asyncio.run(omini.run())
        except KeyboardInterrupt:
            print("\n🔴 Shutting down...")

    threading.Thread(target=runner, daemon=True).start()
    ui.run()


if __name__ == "__main__":
    main()
