import threading
import time
from collections import defaultdict
from queue import Empty, Queue
from typing import Any, Callable


class EventBus:
    """Thread-safe event bus with publish/subscribe and optional queue consumption."""

    def __init__(self, max_queue_size: int = 2000):
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)
        self._queue: Queue[dict[str, Any]] = Queue(maxsize=max_queue_size)
        self._lock = threading.Lock()

    def subscribe(self, event_name: str, callback: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            self._subscribers[event_name].append(callback)

    def publish(self, event_name: str, payload: dict[str, Any] | None = None) -> bool:
        event = {
            "event": event_name,
            "timestamp": time.time(),
            "payload": payload or {},
        }

        try:
            self._queue.put_nowait(event)
        except Exception:
            return False

        callbacks = []
        with self._lock:
            callbacks.extend(self._subscribers.get(event_name, []))
            callbacks.extend(self._subscribers.get("*", []))

        for cb in callbacks:
            try:
                cb(event)
            except Exception:
                continue

        return True

    def next_event(self, timeout: float = 0.2) -> dict[str, Any] | None:
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None


_GLOBAL_BUS: EventBus | None = None


def get_event_bus() -> EventBus:
    global _GLOBAL_BUS
    if _GLOBAL_BUS is None:
        _GLOBAL_BUS = EventBus()
    return _GLOBAL_BUS
