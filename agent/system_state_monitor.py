import threading
import time
import socket
from typing import Any

import psutil

from core.event_bus import get_event_bus


class SystemStateMonitor:
    def __init__(self, poll_seconds: float = 5.0):
        self._poll_seconds = max(1.0, poll_seconds)
        self._running = False
        self._thread: threading.Thread | None = None
        self._bus = get_event_bus()
        self._last_proc_cpu: dict[int, float] = {}
        self._last_snapshot: dict[str, Any] = {}
        self._last_connectivity: bool | None = None
        self._known_removable_mounts: set[str] = set()
        self._alert_cooldowns: dict[str, float] = {}

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="SystemStateMonitor")
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def get_last_snapshot(self) -> dict[str, Any]:
        return dict(self._last_snapshot)

    def _loop(self) -> None:
        while self._running:
            snapshot = self._collect_snapshot()
            self._last_snapshot = dict(snapshot)
            self._bus.publish("system.snapshot", snapshot)
            self._emit_alerts(snapshot)
            time.sleep(self._poll_seconds)

    def _collect_snapshot(self) -> dict[str, Any]:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        internet_online = self._internet_online()
        removable_mounts = self._removable_mounts()

        battery_percent = None
        battery_plugged = None
        try:
            bat = psutil.sensors_battery()
            if bat is not None:
                battery_percent = float(bat.percent)
                battery_plugged = bool(bat.power_plugged)
        except Exception:
            pass

        thermals = {}
        try:
            temps = psutil.sensors_temperatures() or {}
            for key, values in temps.items():
                if values:
                    thermals[key] = max((v.current for v in values if getattr(v, "current", None) is not None), default=None)
        except Exception:
            pass

        top = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                top.append(
                    {
                        "pid": int(proc.info.get("pid") or 0),
                        "name": str(proc.info.get("name") or "unknown"),
                        "cpu": float(proc.info.get("cpu_percent") or 0.0),
                        "mem": float(proc.info.get("memory_percent") or 0.0),
                    }
                )
            except Exception:
                continue

        top.sort(key=lambda p: (p["cpu"], p["mem"]), reverse=True)
        top = top[:15]

        return {
            "cpu_percent": cpu,
            "ram_percent": ram,
            "battery_percent": battery_percent,
            "battery_plugged": battery_plugged,
            "internet_online": internet_online,
            "removable_mounts": removable_mounts,
            "thermals": thermals,
            "top_processes": top,
            "timestamp": time.time(),
        }

    @staticmethod
    def _internet_online(timeout: float = 1.0) -> bool:
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=timeout).close()
            return True
        except Exception:
            return False

    @staticmethod
    def _removable_mounts() -> list[str]:
        mounts: list[str] = []
        for p in psutil.disk_partitions(all=False):
            opts = (p.opts or "").lower()
            if "removable" in opts or "cdrom" in opts:
                mounts.append(p.mountpoint)
        return mounts

    def _emit_alerts(self, snapshot: dict[str, Any]) -> None:
        now = time.time()
        cpu = float(snapshot.get("cpu_percent") or 0.0)
        if cpu >= 85.0 and self._cooldown_ok("high_cpu", now, 90):
            self._bus.publish(
                "system.alert",
                {
                    "severity": "high",
                    "kind": "high_cpu",
                    "message": f"CPU usage is high at {cpu:.1f}%. Suggestion: close heavy browser tabs.",
                },
            )

        gpu_alerted = False
        for label, temp in snapshot.get("thermals", {}).items():
            if temp is None:
                continue
            label_low = str(label).lower()
            if any(key in label_low for key in ("gpu", "nvidia", "amdgpu", "radeon", "video")) and float(temp) >= 80.0:
                if self._cooldown_ok(f"gpu:{label_low}", now, 180):
                    self._bus.publish(
                        "system.alert",
                        {
                            "severity": "high",
                            "kind": "gpu_temp_spike",
                            "gpu": {"label": label, "temp": float(temp)},
                            "message": f"GPU temperature is high on {label}: {float(temp):.1f}°C.",
                        },
                    )
                    gpu_alerted = True

        current_mounts = set(snapshot.get("removable_mounts", []) or [])
        inserted = current_mounts - self._known_removable_mounts
        for mount in sorted(inserted):
            if self._cooldown_ok(f"usb:{mount}", now, 120):
                self._bus.publish(
                    "system.alert",
                    {
                        "severity": "medium",
                        "kind": "usb_inserted",
                        "message": f"Removable drive detected at {mount}.",
                        "mount": mount,
                    },
                )
        self._known_removable_mounts = current_mounts

        for proc in snapshot.get("top_processes", []):
            pid = int(proc["pid"])
            if pid in (0, 4):
                continue
            current_cpu = float(proc["cpu"])
            prev = self._last_proc_cpu.get(pid, 0.0)
            self._last_proc_cpu[pid] = current_cpu
            if current_cpu >= 70.0 and (current_cpu - prev) >= 40.0 and self._cooldown_ok(f"proc:{pid}", now, 180):
                self._bus.publish(
                    "system.alert",
                    {
                        "severity": "high",
                        "kind": "abnormal_process_spike",
                        "message": (
                            f"Process spike: {proc['name']} (PID {pid}) jumped to {current_cpu:.1f}% CPU. "
                            "Suggestion: investigate or terminate process."
                        ),
                        "process": proc,
                    },
                )

    def _cooldown_ok(self, key: str, now: float, cooldown_seconds: int) -> bool:
        last = self._alert_cooldowns.get(key, 0.0)
        if now - last < cooldown_seconds:
            return False
        self._alert_cooldowns[key] = now
        return True


_MONITOR: SystemStateMonitor | None = None


def get_system_state_monitor() -> SystemStateMonitor:
    global _MONITOR
    if _MONITOR is None:
        _MONITOR = SystemStateMonitor()
    return _MONITOR
