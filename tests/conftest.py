from __future__ import annotations

import sys
import types
import importlib


def _install_pyautogui_stub() -> None:
    if "pyautogui" in sys.modules:
        return

    mod = types.ModuleType("pyautogui")
    mod.FAILSAFE = True
    mod.PAUSE = 0.0

    def _noop(*args, **kwargs):
        return None

    class _Shot:
        def save(self, *_args, **_kwargs):
            return None

    mod.press = _noop
    mod.hotkey = _noop
    mod.write = _noop
    mod.click = _noop
    mod.scroll = _noop
    mod.moveTo = _noop
    mod.dragTo = _noop
    mod.screenshot = lambda *_a, **_k: _Shot()
    sys.modules["pyautogui"] = mod


def _install_numpy_stub() -> None:
    if "numpy" in sys.modules:
        return

    mod = types.ModuleType("numpy")
    mod.mean = lambda _arr: 1.0
    mod.array = lambda x: x
    sys.modules["numpy"] = mod


def _install_playwright_stub() -> None:
    if "playwright.async_api" in sys.modules:
        return

    async_api = types.ModuleType("playwright.async_api")

    class _Dummy:
        pass

    async_api.BrowserContext = _Dummy
    async_api.Page = _Dummy
    async_api.Playwright = _Dummy
    async_api.TimeoutError = TimeoutError

    async def _async_playwright():
        raise RuntimeError("playwright stub: not available in tests")

    async_api.async_playwright = _async_playwright
    sys.modules["playwright.async_api"] = async_api

    if "playwright" not in sys.modules:
        root = types.ModuleType("playwright")
        sys.modules["playwright"] = root


def _install_sounddevice_stub() -> None:
    if "sounddevice" in sys.modules:
        return

    mod = types.ModuleType("sounddevice")

    class _RawOutputStream:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def start(self):
            return None

        def write(self, _chunk):
            return None

        def stop(self):
            return None

        def close(self):
            return None

    mod.RawOutputStream = _RawOutputStream
    sys.modules["sounddevice"] = mod


def _alias_project_config_module() -> None:
    if "config" in sys.modules:
        return
    try:
        sys.modules["config"] = importlib.import_module("OMINI_ASSISTANT_AI.config")
    except Exception:
        pass


def _install_google_stubs() -> None:
    if "google.generativeai" not in sys.modules:
        gmod = types.ModuleType("google.generativeai")

        class _Resp:
            def __init__(self, text: str = "{}"):
                self.text = text

        class _GenModel:
            def __init__(self, *_args, **_kwargs):
                pass

            def generate_content(self, *_args, **_kwargs):
                return _Resp("{}")

        gmod.configure = lambda **_kwargs: None
        gmod.GenerativeModel = _GenModel
        sys.modules["google.generativeai"] = gmod

    if "google.genai" not in sys.modules:
        genai_mod = types.ModuleType("google.genai")

        types_mod = types.ModuleType("google.genai.types")

        class _SimpleCfg:
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs

        types_mod.LiveConnectConfig = _SimpleCfg
        types_mod.SpeechConfig = _SimpleCfg
        types_mod.VoiceConfig = _SimpleCfg
        types_mod.PrebuiltVoiceConfig = _SimpleCfg
        sys.modules["google.genai.types"] = types_mod

        class _Models:
            def generate_content(self, *_args, **_kwargs):
                part = types.SimpleNamespace(text="stubbed response")
                candidate = types.SimpleNamespace(content=types.SimpleNamespace(parts=[part]))
                return types.SimpleNamespace(candidates=[candidate])

        class _Client:
            def __init__(self, *args, **kwargs):
                self.models = _Models()

        genai_mod.Client = _Client
        genai_mod.types = types_mod
        sys.modules["google.genai"] = genai_mod

    if "google" not in sys.modules:
        google_mod = types.ModuleType("google")
        sys.modules["google"] = google_mod

    if "google" in sys.modules and "google.genai" in sys.modules:
        setattr(sys.modules["google"], "genai", sys.modules["google.genai"])


_install_pyautogui_stub()
_install_numpy_stub()
_install_playwright_stub()
_install_sounddevice_stub()
_install_google_stubs()
_alias_project_config_module()
