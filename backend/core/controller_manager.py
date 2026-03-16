import threading

from backend.core.assistant_controller import AssistantController


class ControllerManager:
    """Provide isolated controller instances per interaction scope."""

    def __init__(self, controller_factory=None):
        self._controller_factory = controller_factory or AssistantController
        self._controllers = {}
        self._lock = threading.RLock()

    def get_controller(self, scope: str) -> AssistantController:
        """Return a stable controller instance for the provided scope."""
        normalized_scope = str(scope or "default")
        with self._lock:
            controller = self._controllers.get(normalized_scope)
            if controller is None:
                controller = self._controller_factory()
                self._controllers[normalized_scope] = controller
            return controller

    def has_pending_confirmation(self, scope: str) -> bool:
        """Check whether the scoped controller is waiting for confirmation."""
        with self._lock:
            controller = self._controllers.get(str(scope or "default"))
            return bool(controller and controller.has_pending_confirmation())

    def get_pending_confirmation(self, scope: str):
        """Return the pending confirmation payload for a scope, if any."""
        with self._lock:
            controller = self._controllers.get(str(scope or "default"))
            if not controller:
                return None
            return controller.get_pending_confirmation()

    def has_any_pending_confirmation(self) -> bool:
        """Return True when any managed controller is awaiting confirmation."""
        with self._lock:
            return any(controller.has_pending_confirmation() for controller in self._controllers.values())