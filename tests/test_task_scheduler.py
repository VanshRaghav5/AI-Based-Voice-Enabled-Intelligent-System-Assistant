import os
import sys
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


from backend.database import Base
from backend.database.models import ScheduledTask, User
from backend.scheduling.task_scheduler import TaskSchedulerService


class FakeController:
    def __init__(self):
        self.calls = []

    def process(self, command, language=None):
        self.calls.append((command, language))
        return {
            "status": "success",
            "message": f"Executed scheduled command: {command}",
            "data": {},
        }


class FakeControllerManager:
    def __init__(self):
        self.controllers = {}

    def get_controller(self, scope):
        if scope not in self.controllers:
            self.controllers[scope] = FakeController()
        return self.controllers[scope]


@pytest.fixture
def scheduler_context():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    manager = FakeControllerManager()
    scheduler_service = TaskSchedulerService(
        controller_manager=manager,
        session_factory=TestingSessionLocal,
        auto_start=True,
    )

    session = TestingSessionLocal()
    user = User(username="scheduler_user", email="scheduler@example.com", hashed_password="hash")
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()

    try:
        yield TestingSessionLocal, scheduler_service, manager, user
    finally:
        scheduler_service.shutdown()
        Base.metadata.drop_all(bind=engine)


def test_task_scheduler_creates_and_deletes_interval_task(scheduler_context):
    session_factory, scheduler_service, _, user = scheduler_context

    task = scheduler_service.create_task(
        user_id=user.id,
        name="Hourly volume check",
        command="increase volume",
        language="english",
        trigger_type="interval",
        interval_seconds=3600,
        run_at=datetime.utcnow() + timedelta(minutes=5),
    )

    assert task["id"] is not None
    assert task["trigger_type"] == "interval"
    assert task["next_run_at"] is not None
    assert scheduler_service.scheduler.get_job(scheduler_service._job_id(task["id"])) is not None

    listed = scheduler_service.list_tasks_for_user(user.id)
    assert len(listed) == 1
    assert listed[0]["name"] == "Hourly volume check"

    deleted = scheduler_service.delete_task(user.id, task["id"])
    assert deleted is True
    assert scheduler_service.scheduler.get_job(scheduler_service._job_id(task["id"])) is None
    assert scheduler_service.list_tasks_for_user(user.id) == []


def test_task_scheduler_executes_one_time_task_and_marks_it_complete(scheduler_context):
    session_factory, scheduler_service, manager, user = scheduler_context

    task = scheduler_service.create_task(
        user_id=user.id,
        name="One-time browser task",
        command="open youtube",
        language="english",
        trigger_type="one_time",
        run_at=datetime.utcnow() + timedelta(minutes=10),
    )

    scheduler_service._execute_task_job(task["id"])

    session = session_factory()
    stored_task = session.query(ScheduledTask).filter(ScheduledTask.id == task["id"]).first()
    session.close()

    assert stored_task is not None
    assert stored_task.last_status == "success"
    assert stored_task.is_active is False
    assert manager.get_controller(f"user:{user.id}").calls == [("open youtube", "english")]