from datetime import datetime
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.utils.logger import logger
from backend.models.models import ScheduledTask


class TaskSchedulerService:
    """Persist, schedule, and execute recurring user automation tasks."""

    def __init__(self, controller_manager, socketio=None, session_factory=None, scheduler=None, auto_start=False):
        self.controller_manager = controller_manager
        self.socketio = socketio
        self.session_factory = session_factory
        self.scheduler = scheduler or BackgroundScheduler(timezone="UTC")
        self._lock = threading.RLock()
        self._started = False

        if auto_start:
            self.start()

    def start(self):
        """Start the background scheduler and hydrate persisted tasks."""
        with self._lock:
            if self._started:
                return
            self.scheduler.start()
            self._started = True
            self.load_persisted_tasks()
            logger.info("[TaskScheduler] Scheduler started")

    def shutdown(self):
        """Stop the background scheduler."""
        with self._lock:
            if not self._started:
                return
            self.scheduler.shutdown(wait=False)
            self._started = False
            logger.info("[TaskScheduler] Scheduler stopped")

    def _job_id(self, task_id: int) -> str:
        return f"scheduled-task:{task_id}"

    def _ensure_started(self):
        if not self._started:
            self.start()

    def _serialize_task(self, task: ScheduledTask) -> dict:
        return {
            "id": task.id,
            "user_id": task.user_id,
            "name": task.name,
            "command": task.command,
            "language": task.language,
            "trigger_type": task.trigger_type,
            "run_at": task.run_at.isoformat() if task.run_at else None,
            "interval_seconds": task.interval_seconds,
            "cron_expression": task.cron_expression,
            "is_active": task.is_active,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
            "next_run_at": task.next_run_at.isoformat() if task.next_run_at else None,
            "last_status": task.last_status,
            "last_message": task.last_message,
        }

    def _build_trigger(self, task: ScheduledTask):
        if task.trigger_type == "one_time":
            if not task.run_at:
                raise ValueError("run_at is required for one_time schedules")
            return DateTrigger(run_date=task.run_at)

        if task.trigger_type == "interval":
            if not task.interval_seconds:
                raise ValueError("interval_seconds is required for interval schedules")
            return IntervalTrigger(seconds=task.interval_seconds, start_date=task.run_at)

        if task.trigger_type == "cron":
            if not task.cron_expression:
                raise ValueError("cron_expression is required for cron schedules")
            return CronTrigger.from_crontab(task.cron_expression)

        raise ValueError(f"Unsupported trigger_type: {task.trigger_type}")

    def _update_next_run_at(self, db, task_id: int):
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if not task:
            return None
        job = self.scheduler.get_job(self._job_id(task_id))
        task.next_run_at = job.next_run_time if job else None
        db.commit()
        db.refresh(task)
        return task

    def _schedule_task(self, task_id: int):
        db = self.session_factory()
        try:
            task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task or not task.is_active:
                return None

            if task.trigger_type == "one_time" and task.run_at and task.run_at <= datetime.utcnow():
                task.is_active = False
                task.last_status = "error"
                task.last_message = "Scheduled time is in the past."
                db.commit()
                db.refresh(task)
                return task

            trigger = self._build_trigger(task)
            self.scheduler.add_job(
                self._execute_task_job,
                trigger=trigger,
                args=[task.id],
                id=self._job_id(task.id),
                replace_existing=True,
                coalesce=True,
                misfire_grace_time=300,
            )
            return self._update_next_run_at(db, task.id)
        finally:
            db.close()

    def load_persisted_tasks(self):
        """Load active persisted tasks into the in-memory scheduler."""
        if not self.session_factory:
            return

        db = self.session_factory()
        try:
            active_tasks = db.query(ScheduledTask).filter(ScheduledTask.is_active.is_(True)).all()
            for task in active_tasks:
                try:
                    self._schedule_task(task.id)
                except Exception as exc:
                    logger.error(f"[TaskScheduler] Failed to load task {task.id}: {exc}")
        finally:
            db.close()

    def create_task(self, user_id: int, name: str, command: str, trigger_type: str, language: str = None, run_at=None, interval_seconds=None, cron_expression=None):
        """Persist and schedule a new task for a user."""
        self._ensure_started()
        db = self.session_factory()
        try:
            task = ScheduledTask(
                user_id=user_id,
                name=(name or command[:80]).strip(),
                command=command.strip(),
                language=language,
                trigger_type=trigger_type,
                run_at=run_at,
                interval_seconds=interval_seconds,
                cron_expression=cron_expression.strip() if isinstance(cron_expression, str) else cron_expression,
                is_active=True,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
        finally:
            db.close()

        scheduled = self._schedule_task(task.id)
        if scheduled is None:
            raise ValueError("Failed to schedule task")
        return self._serialize_task(scheduled)

    def list_tasks_for_user(self, user_id: int) -> list:
        db = self.session_factory()
        try:
            tasks = (
                db.query(ScheduledTask)
                .filter(ScheduledTask.user_id == user_id)
                .order_by(ScheduledTask.created_at.desc())
                .all()
            )
            return [self._serialize_task(task) for task in tasks]
        finally:
            db.close()

    def delete_task(self, user_id: int, task_id: int) -> bool:
        db = self.session_factory()
        try:
            task = (
                db.query(ScheduledTask)
                .filter(ScheduledTask.id == task_id, ScheduledTask.user_id == user_id)
                .first()
            )
            if not task:
                return False

            job = self.scheduler.get_job(self._job_id(task.id))
            if job:
                self.scheduler.remove_job(self._job_id(task.id))

            db.delete(task)
            db.commit()
            return True
        finally:
            db.close()

    def _execute_task_job(self, task_id: int):
        """Execute a scheduled automation command for a persisted task."""
        db = self.session_factory()
        try:
            task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if not task or not task.is_active:
                return

            controller = self.controller_manager.get_controller(f"user:{task.user_id}")
            result = controller.process(task.command, language=task.language)

            task.last_run_at = datetime.utcnow()
            task.last_status = result.get("status", "success")
            task.last_message = str(result.get("message", "Task executed"))[:500]

            if task.trigger_type == "one_time":
                task.is_active = False
                scheduled_job = self.scheduler.get_job(self._job_id(task.id))
                if scheduled_job:
                    self.scheduler.remove_job(self._job_id(task.id))

            db.commit()
            db.refresh(task)

            job = self.scheduler.get_job(self._job_id(task.id))
            task.next_run_at = job.next_run_time if job else None
            db.commit()
            db.refresh(task)

            if self.socketio:
                self.socketio.emit('scheduled_task_result', {
                    'task': self._serialize_task(task),
                    'result': result,
                })
        except Exception as exc:
            logger.error(f"[TaskScheduler] Task {task_id} failed: {exc}", exc_info=True)
            task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
            if task:
                task.last_run_at = datetime.utcnow()
                task.last_status = "error"
                task.last_message = str(exc)[:500]
                db.commit()
        finally:
            db.close()