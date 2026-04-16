# backend/automation/coding/terminal_tool.py

import os
import re
import subprocess
import time
from typing import Dict, Any, Optional

from backend.automation.base_tool import BaseTool
from backend.automation.error_handler import error_handler, AutomationError
from backend.config.logger import logger


# ---------------------------------------------------------------------------
# Module-level registry for background processes started by the assistant.
# ---------------------------------------------------------------------------
_background_processes: Dict[int, Dict[str, Any]] = {}


def _default_workspace() -> str:
    """Return the configured default workspace or fall back to cwd."""
    try:
        from backend.config.assistant_config import assistant_config
        configured = assistant_config.get("assistant.default_workspace", "")
        if configured and os.path.isdir(configured):
            return os.path.abspath(configured)
    except Exception:
        pass
    return os.getcwd()


# ---------------------------------------------------------------------------
# Blocked command patterns — hard-rejected, even with confirmation.
# ---------------------------------------------------------------------------
_BLOCKED_PATTERNS = [
    # Linux / macOS
    re.compile(r"rm\s+-rf\s+/", re.IGNORECASE),
    re.compile(r"mkfs\.", re.IGNORECASE),
    re.compile(r":\(\)\{", re.IGNORECASE),           # fork bomb
    # Windows
    re.compile(r"rmdir\s+/s\s+/q\s+[a-z]:\\", re.IGNORECASE),
    re.compile(r"del\s+/[sq]", re.IGNORECASE),
    re.compile(r"format\s+[a-z]:", re.IGNORECASE),
]


def _is_blocked(command: str) -> bool:
    """Return True if *command* matches a destructive pattern."""
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(command):
            return True
    return False


# ---------------------------------------------------------------------------
# Output truncation helpers
# ---------------------------------------------------------------------------
MAX_OUTPUT_LINES = 200
MAX_OUTPUT_BYTES = 20_480   # 20 KB
TTS_TAIL_LINES = 10


def _truncate_output(raw: str) -> tuple:
    """Return ``(truncated_text, was_truncated)``."""
    if not raw:
        return "", False

    # Byte-level truncation first.
    encoded = raw.encode("utf-8", errors="replace")
    if len(encoded) > MAX_OUTPUT_BYTES:
        raw = encoded[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
        was_truncated = True
    else:
        was_truncated = False

    lines = raw.splitlines()
    if len(lines) > MAX_OUTPUT_LINES:
        lines = lines[:MAX_OUTPUT_LINES]
        was_truncated = True

    return "\n".join(lines), was_truncated


def _tts_summary(output: str, return_code: int) -> str:
    """Build a short spoken summary: exit code + last few lines."""
    lines = output.strip().splitlines() if output else []
    tail = lines[-TTS_TAIL_LINES:] if len(lines) > TTS_TAIL_LINES else lines

    if return_code == 0:
        prefix = "Command completed successfully."
    else:
        prefix = f"Command failed with exit code {return_code}."

    if not tail:
        return prefix

    snippet = " | ".join(line.strip() for line in tail if line.strip())
    # Cap spoken text to reasonable TTS length.
    if len(snippet) > 400:
        snippet = snippet[:397] + "..."
    return f"{prefix} Output: {snippet}"


# ===================================================================
# Tool: terminal.run
# ===================================================================

class TerminalRunTool(BaseTool):
    name = "terminal.run"
    description = "Run a terminal command and return output"
    risk_level = "high"
    requires_confirmation = True

    def execute(
        self,
        command: str,
        cwd: str = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        resolved_cwd = os.path.abspath(cwd) if cwd else _default_workspace()

        def _run():
            # --- Validate ---
            if not command or not command.strip():
                raise AutomationError(
                    "Empty command",
                    "I need a command to run. Please specify what to execute.",
                )

            if _is_blocked(command):
                logger.warning(f"[Terminal] BLOCKED dangerous command: {command}")
                raise AutomationError(
                    f"Blocked dangerous command: {command}",
                    "That command is blocked because it could cause serious damage to your system.",
                )

            if not os.path.isdir(resolved_cwd):
                raise AutomationError(
                    f"Working directory does not exist: {resolved_cwd}",
                    f"The directory {resolved_cwd} does not exist.",
                )

            logger.info(f"[Terminal] Running: {command}  (cwd={resolved_cwd}, timeout={timeout}s)")

            # --- Execute ---
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=resolved_cwd,
                    timeout=timeout,
                    capture_output=True,
                    text=True,
                )
            except subprocess.TimeoutExpired:
                raise AutomationError(
                    f"Command timed out after {timeout}s: {command}",
                    f"The command timed out after {timeout} seconds.",
                )
            except Exception as exc:
                raise AutomationError(str(exc), f"Failed to run command: {exc}")

            combined = (result.stdout or "") + (result.stderr or "")
            output, truncated = _truncate_output(combined)
            line_count = len(output.splitlines()) if output else 0

            # Store full output in session memory for later recall.
            try:
                from backend.memory.memory_store import MemoryStore
                store = MemoryStore()
                store.update({"last_terminal_output": output})
            except Exception as mem_exc:
                logger.debug(f"[Terminal] Could not persist output to memory: {mem_exc}")

            spoken = _tts_summary(output, result.returncode)

            return {
                "status": "success" if result.returncode == 0 else "error",
                "message": spoken,
                "data": {
                    "command": command,
                    "cwd": resolved_cwd,
                    "return_code": result.returncode,
                    "output": output,
                    "output_lines": line_count,
                    "truncated": truncated,
                },
            }

        return error_handler.wrap_automation(
            func=_run,
            operation_name="Terminal Run",
            context={"command": command, "cwd": resolved_cwd},
        )


# ===================================================================
# Tool: terminal.run_background
# ===================================================================

class TerminalRunBackgroundTool(BaseTool):
    name = "terminal.run_background"
    description = "Run a long-running command in background (dev servers, watchers)"
    risk_level = "high"
    requires_confirmation = True

    def execute(self, command: str, cwd: str = None) -> Dict[str, Any]:
        resolved_cwd = os.path.abspath(cwd) if cwd else _default_workspace()

        def _run_bg():
            if not command or not command.strip():
                raise AutomationError(
                    "Empty command",
                    "I need a command to run in the background.",
                )

            if _is_blocked(command):
                logger.warning(f"[Terminal] BLOCKED dangerous background command: {command}")
                raise AutomationError(
                    f"Blocked dangerous command: {command}",
                    "That command is blocked because it could cause serious damage.",
                )

            if not os.path.isdir(resolved_cwd):
                raise AutomationError(
                    f"Working directory does not exist: {resolved_cwd}",
                    f"The directory {resolved_cwd} does not exist.",
                )

            logger.info(f"[Terminal] Starting background: {command}  (cwd={resolved_cwd})")

            try:
                proc = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=resolved_cwd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as exc:
                raise AutomationError(str(exc), f"Failed to start background command: {exc}")

            _background_processes[proc.pid] = {
                "command": command,
                "cwd": resolved_cwd,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "process": proc,
            }

            logger.info(f"[Terminal] Background process started: PID {proc.pid}")

            return {
                "status": "success",
                "message": f"Started background process (PID {proc.pid}): {command}",
                "data": {
                    "pid": proc.pid,
                    "command": command,
                    "cwd": resolved_cwd,
                },
            }

        return error_handler.wrap_automation(
            func=_run_bg,
            operation_name="Terminal Run Background",
            context={"command": command, "cwd": resolved_cwd},
        )


# ===================================================================
# Tool: terminal.kill
# ===================================================================

class TerminalKillTool(BaseTool):
    name = "terminal.kill"
    description = "Kill a background process by PID (kills most recent if PID omitted)"
    risk_level = "medium"
    requires_confirmation = False

    def execute(self, pid: int = None) -> Dict[str, Any]:

        def _kill():
            if not _background_processes:
                return {
                    "status": "error",
                    "message": "There are no background processes to stop.",
                    "data": {},
                }

            # Resolve target PID.
            target_pid: Optional[int] = None
            if pid is not None:
                target_pid = int(pid)
            else:
                # Kill the most recently started process.
                target_pid = max(_background_processes.keys())

            entry = _background_processes.get(target_pid)
            if entry is None:
                return {
                    "status": "error",
                    "message": f"No tracked background process with PID {target_pid}.",
                    "data": {"pid": target_pid},
                }

            proc = entry.get("process")
            cmd_label = entry.get("command", "unknown")
            killed = False

            if proc is not None:
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=3)
                    killed = True
                except Exception as exc:
                    logger.warning(f"[Terminal] Error killing PID {target_pid}: {exc}")
                    # Attempt force-kill via OS as last resort.
                    try:
                        import signal
                        os.kill(target_pid, signal.SIGTERM)
                        killed = True
                    except Exception:
                        pass

            _background_processes.pop(target_pid, None)
            logger.info(f"[Terminal] Killed background process PID {target_pid} ({cmd_label})")

            return {
                "status": "success",
                "message": f"Stopped background process (PID {target_pid}): {cmd_label}",
                "data": {
                    "pid": target_pid,
                    "command": cmd_label,
                    "killed": killed,
                },
            }

        return error_handler.wrap_automation(
            func=_kill,
            operation_name="Terminal Kill",
            context={"pid": pid},
        )


# ===================================================================
# Tool: terminal.list_running
# ===================================================================

class TerminalListRunningTool(BaseTool):
    name = "terminal.list_running"
    description = "List all background processes started by the assistant"
    risk_level = "low"
    requires_confirmation = False

    def execute(self) -> Dict[str, Any]:

        def _list():
            alive = []
            dead_pids = []

            for proc_pid, entry in _background_processes.items():
                proc = entry.get("process")
                is_alive = proc is not None and proc.poll() is None

                item = {
                    "pid": proc_pid,
                    "command": entry.get("command", ""),
                    "cwd": entry.get("cwd", ""),
                    "started_at": entry.get("started_at", ""),
                    "alive": is_alive,
                }

                if is_alive:
                    alive.append(item)
                else:
                    dead_pids.append(proc_pid)

            # Prune dead processes from the registry.
            for dp in dead_pids:
                _background_processes.pop(dp, None)

            if not alive:
                return {
                    "status": "success",
                    "message": "No background processes are currently running.",
                    "data": {"processes": []},
                }

            desc = ", ".join(f"PID {p['pid']}: {p['command']}" for p in alive)
            return {
                "status": "success",
                "message": f"{len(alive)} background process(es) running: {desc}",
                "data": {"processes": alive},
            }

        return error_handler.wrap_automation(
            func=_list,
            operation_name="Terminal List Running",
            context={},
        )
