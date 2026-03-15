from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from desktop.services.api_client import ApiClient


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, api: ApiClient, parent=None):
        super().__init__(parent)
        self.api = api

        self.setWindowTitle("OmniAssist — Sign in")
        self.setModal(True)
        self.setMinimumWidth(420)

        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QtWidgets.QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.error = QtWidgets.QLabel("")
        self.error.setWordWrap(True)
        self.error.setStyleSheet("color: #ff6b6b;")

        self.btn_login = QtWidgets.QPushButton("Sign in")
        self.btn_login.clicked.connect(self._on_login)
        self.btn_login.setDefault(True)

        form = QtWidgets.QFormLayout()
        form.addRow("Username", self.username)
        form.addRow("Password", self.password)

        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("Welcome back")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        subtitle = QtWidgets.QLabel("Sign in to connect to your local assistant backend.")
        subtitle.setStyleSheet("color: #a8a8a8;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addWidget(self.error)
        layout.addWidget(self.btn_login)

        self.username.returnPressed.connect(self._on_login)
        self.password.returnPressed.connect(self._on_login)

    @QtCore.Slot()
    def _on_login(self):
        self.error.setText("")
        u = self.username.text().strip()
        p = self.password.text()
        if not u or not p:
            self.error.setText("Please enter username and password.")
            return

        self.btn_login.setEnabled(False)
        ok, msg, token, user = self.api.login(u, p)
        self.btn_login.setEnabled(True)

        if ok:
            self.accept()
        else:
            self.error.setText(msg or "Login failed")
