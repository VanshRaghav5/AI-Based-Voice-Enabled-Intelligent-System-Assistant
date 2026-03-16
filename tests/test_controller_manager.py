import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


from backend.core.controller_manager import ControllerManager


class DummyController:
    def __init__(self):
        self.pending = False
        self.payload = None

    def has_pending_confirmation(self):
        return self.pending

    def get_pending_confirmation(self):
        return self.payload


def test_controller_manager_reuses_scope_instances():
    manager = ControllerManager(controller_factory=DummyController)

    first = manager.get_controller("user:1")
    second = manager.get_controller("user:1")
    third = manager.get_controller("user:2")

    assert first is second
    assert first is not third


def test_controller_manager_tracks_pending_confirmation_per_scope():
    manager = ControllerManager(controller_factory=DummyController)

    first = manager.get_controller("user:1")
    second = manager.get_controller("user:2")

    first.pending = True
    first.payload = {"status": "confirmation_required", "message": "confirm first"}

    assert manager.has_pending_confirmation("user:1") is True
    assert manager.has_pending_confirmation("user:2") is False
    assert manager.has_any_pending_confirmation() is True
    assert manager.get_pending_confirmation("user:1") == first.payload

    second.pending = True
    second.payload = {"status": "confirmation_required", "message": "confirm second"}

    assert manager.get_pending_confirmation("user:2") == second.payload