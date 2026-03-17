from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from desktop.config import load_config
from desktop.core.event_bus import EventBus
from desktop.services.api_client import ApiClient
from desktop.services.session_store import SessionStore
from desktop.ui.login_dialog import LoginDialog
from desktop.ui.main_window import MainWindow


def _configure_qt() -> None:
    QtCore.QCoreApplication.setOrganizationName("OmniAssist")
    QtCore.QCoreApplication.setApplicationName("OmniAssist")
    QtCore.QCoreApplication.setApplicationVersion("2.0")
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)


def run() -> int:
    _configure_qt()

    app = QtWidgets.QApplication(sys.argv)

    theme_path = Path(__file__).resolve().parent / "themes" / "dark.qss"
    if theme_path.exists():
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    config = load_config()
    session = SessionStore()
    bus = EventBus()
    api = ApiClient(base_url=config.base_url, session=session)

    # Attempt silent token verify.
    is_valid, user = api.verify_token()
    if not is_valid:
        dlg = LoginDialog(api=api)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return 0

    window = MainWindow(config=config, api=api, session=session, bus=bus)
    window.show()

    return app.exec()
