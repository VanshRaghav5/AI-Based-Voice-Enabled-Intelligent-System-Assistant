import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable

from core.event_bus import get_event_bus


@dataclass
class ScheduledJob:
    job_id: str
    name: str
    interval_seconds: int
    action: str
    payload: dict
    next_run_at: float
    enabled: bool = True


class BackgroundScheduler:
    def __init__(self):
        self._jobs: dict[str, ScheduledJob] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._bus = get_event_bus()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="BackgroundScheduler")
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def schedule(self, name: str, interval_seconds: int, action: str, payload: dict | None = None) -> str:
        with self._lock:
            for existing in self._jobs.values():
                if existing.name == name:
                    existing.interval_seconds = max(10, int(interval_seconds))
                    existing.action = action
                    existing.payload = payload or {}
                    existing.enabled = True
                    existing.next_run_at = time.time() + existing.interval_seconds
                    return existing.job_id

        jid = uuid.uuid4().hex[:10]
        job = ScheduledJob(
            job_id=jid,
            name=name,
            interval_seconds=max(10, int(interval_seconds)),
            action=action,
            payload=payload or {},
            next_run_at=time.time() + max(10, int(interval_seconds)),
        )
        with self._lock:
            self._jobs[jid] = job
        return jid

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None

    def list_jobs(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "job_id": j.job_id,
                    "name": j.name,
                    "interval_seconds": j.interval_seconds,
                    "action": j.action,
                    "next_run_in": max(0, int(j.next_run_at - time.time())),
                    "enabled": j.enabled,
                }
                for j in self._jobs.values()
            ]

    def _loop(self) -> None:
        while self._running:
            now = time.time()
            due: list[ScheduledJob] = []
            with self._lock:
                for job in self._jobs.values():
                    if job.enabled and now >= job.next_run_at:
                        due.append(job)
                        job.next_run_at = now + job.interval_seconds

            for job in due:
                self._bus.publish(
                    "scheduler.job_due",
                    {
                        "job_id": job.job_id,
                        "name": job.name,
                        "action": job.action,
                        "payload": job.payload,
                    },
                )
            time.sleep(1.0)


_SCHED: BackgroundScheduler | None = None


def get_background_scheduler() -> BackgroundScheduler:
    global _SCHED
    if _SCHED is None:
        _SCHED = BackgroundScheduler()
    return _SCHED
