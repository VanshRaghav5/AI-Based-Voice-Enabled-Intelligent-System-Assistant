import threading

from core.event_bus import get_event_bus


class EventAutomationEngine:
    def __init__(self):
        self._bus = get_event_bus()
        self._started = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True

        self._bus.subscribe("system.alert", self._on_system_alert)
        self._bus.subscribe("scheduler.job_due", self._on_scheduler_job)

    def _on_system_alert(self, event: dict) -> None:
        payload = event.get("payload", {})
        kind = payload.get("kind", "unknown")

        if kind == "high_cpu":
            self._bus.publish(
                "assistant.suggestion",
                {
                    "message": "CPU is above 85%. Suggestion: close heavy browser tabs or stop a high-CPU process.",
                    "source": "event_automation",
                },
            )

        if kind == "gpu_temp_spike":
            gpu = payload.get("gpu", {})
            self._bus.publish(
                "assistant.suggestion",
                {
                    "message": (
                        f"GPU temperature is high: {gpu.get('label', 'GPU')} at {gpu.get('temp', '?')}°C. "
                        "Suggestion: reduce graphics load or check cooling."
                    ),
                    "source": "event_automation",
                },
            )

        if kind == "usb_inserted":
            mount = payload.get("mount", "")
            self._bus.publish(
                "assistant.suggestion",
                {
                    "message": (
                        f"USB inserted at {mount}. Suggestion: run duplicate scan or quick safety check on this drive."
                    ),
                    "source": "event_automation",
                },
            )

    def _on_scheduler_job(self, event: dict) -> None:
        payload = event.get("payload", {})
        action = payload.get("action", "")
        data = payload.get("payload", {})

        if action == "drink_water_reminder":
            self._bus.publish(
                "assistant.suggestion",
                {
                    "message": data.get("message", "Hydration reminder: drink water."),
                    "source": "scheduler",
                },
            )


_ENGINE: EventAutomationEngine | None = None


def get_event_automation_engine() -> EventAutomationEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = EventAutomationEngine()
    return _ENGINE
