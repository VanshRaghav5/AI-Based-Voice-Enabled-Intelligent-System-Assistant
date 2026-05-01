import platform
import subprocess
import time
from typing import Any

import psutil


_OS = platform.system()


def _run(cmd: list[str]) -> tuple[bool, str]:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        if out.returncode == 0:
            return True, (out.stdout or "OK").strip() or "OK"
        return False, (out.stderr or out.stdout or "Command failed").strip()
    except Exception as e:
        return False, str(e)


def _shutdown_in(minutes: int) -> tuple[bool, str]:
    if _OS == "Windows":
        return _run(["shutdown", "/s", "/t", str(max(0, minutes * 60))])
    if _OS == "Darwin":
        return _run(["sudo", "shutdown", "-h", f"+{max(0, minutes)}"])
    return _run(["shutdown", "-h", f"+{max(0, minutes)}"])


def _restart_in(minutes: int) -> tuple[bool, str]:
    if _OS == "Windows":
        return _run(["shutdown", "/r", "/t", str(max(0, minutes * 60))])
    if _OS == "Darwin":
        return _run(["sudo", "shutdown", "-r", f"+{max(0, minutes)}"])
    return _run(["shutdown", "-r", f"+{max(0, minutes)}"])


def _sleep_now() -> tuple[bool, str]:
    if _OS == "Windows":
        return _run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    if _OS == "Darwin":
        return _run(["pmset", "sleepnow"])
    return _run(["systemctl", "suspend"])


def _lock_system() -> tuple[bool, str]:
    if _OS == "Windows":
        return _run(["rundll32.exe", "user32.dll,LockWorkStation"])
    if _OS == "Darwin":
        return _run([
            "osascript",
            "-e",
            'tell application "System Events" to keystroke "q" using {control down, command down}',
        ])
    return _run(["loginctl", "lock-session"])


def _kill_process(name: str = "", pid: int | None = None) -> tuple[bool, str]:
    if pid is not None:
        try:
            proc = psutil.Process(int(pid))
            proc.terminate()
            return True, f"Terminated PID {pid} ({proc.name()})"
        except Exception as e:
            return False, str(e)

    if not name:
        return False, "Provide process_name or pid."

    killed = 0
    for proc in psutil.process_iter(["name", "pid"]):
        pname = (proc.info.get("name") or "").lower()
        if pname == name.lower() or pname.startswith(name.lower()):
            try:
                proc.terminate()
                killed += 1
            except Exception:
                continue

    if killed == 0:
        return False, f"No process matched '{name}'."
    return True, f"Terminated {killed} process(es) matching '{name}'."


def _list_processes(limit: int = 25) -> str:
    rows: list[str] = []
    items = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            items.append(
                (
                    float(proc.info.get("cpu_percent") or 0.0),
                    float(proc.info.get("memory_percent") or 0.0),
                    int(proc.info.get("pid") or 0),
                    str(proc.info.get("name") or "unknown"),
                )
            )
        except Exception:
            continue

    items.sort(reverse=True)
    for cpu, mem, pid, name in items[: max(1, min(limit, 100))]:
        rows.append(f"PID={pid:<6} CPU={cpu:>5.1f}% MEM={mem:>5.1f}% {name}")
    return "Top active processes:\n" + "\n".join(rows)


def system_control_agent(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    action = str(params.get("action", "")).strip().lower()

    if action == "lock":
        ok, msg = _lock_system()
        return f"Locked system." if ok else f"Lock failed: {msg}"

    if action == "shutdown":
        ok, msg = _shutdown_in(0)
        return "Shutdown initiated." if ok else f"Shutdown failed: {msg}"

    if action == "shutdown_in":
        mins = int(params.get("minutes", 5))
        ok, msg = _shutdown_in(mins)
        return f"Shutdown scheduled in {mins} minute(s)." if ok else f"Schedule failed: {msg}"

    if action == "restart":
        ok, msg = _restart_in(0)
        return "Restart initiated." if ok else f"Restart failed: {msg}"

    if action == "restart_in":
        mins = int(params.get("minutes", 5))
        ok, msg = _restart_in(mins)
        return f"Restart scheduled in {mins} minute(s)." if ok else f"Schedule failed: {msg}"

    if action == "sleep":
        ok, msg = _sleep_now()
        return "Sleep initiated." if ok else f"Sleep failed: {msg}"

    if action == "kill_process":
        pname = str(params.get("process_name", "")).strip()
        pid = params.get("pid")
        pid_val = int(pid) if pid is not None and str(pid).strip() else None
        ok, msg = _kill_process(name=pname, pid=pid_val)
        return msg if ok else f"Kill failed: {msg}"

    if action == "list_processes":
        return _list_processes(limit=int(params.get("limit", 25)))

    return (
        "Unknown action. Use one of: lock, shutdown, shutdown_in, restart, "
        "restart_in, sleep, kill_process, list_processes."
    )
