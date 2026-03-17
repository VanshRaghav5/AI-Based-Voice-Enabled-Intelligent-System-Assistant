from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from desktop.services.api_client import ApiClient


class RegisterDialog(QtWidgets.QDialog):
    def __init__(self, api: ApiClient, parent=None):
        super().__init__(parent)
        self.api = api

        self.setWindowTitle("OmniAssist — Create account")
        self.setModal(True)
        self.setMinimumWidth(420)

        self.username = QtWidgets.QLineEdit()
        self.username.setPlaceholderText("Username")

        self.email = QtWidgets.QLineEdit()
        self.email.setPlaceholderText("Email")

        self.password = QtWidgets.QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.password2 = QtWidgets.QLineEdit()
        self.password2.setPlaceholderText("Confirm password")
        self.password2.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.error = QtWidgets.QLabel("")
        self.error.setWordWrap(True)
        self.error.setStyleSheet("color: #ff6b6b;")

        self.btn_create = QtWidgets.QPushButton("Create account")
        self.btn_create.clicked.connect(self._on_create)
        self.btn_create.setDefault(True)

        form = QtWidgets.QFormLayout()
        form.addRow("Username", self.username)
        form.addRow("Email", self.email)
        form.addRow("Password", self.password)
        form.addRow("Confirm", self.password2)

        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel("Create your account")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        subtitle = QtWidgets.QLabel("First account becomes admin.")
        subtitle.setStyleSheet("color: #a8a8a8;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(form)
        layout.addWidget(self.error)
        layout.addWidget(self.btn_create)

        self.username.returnPressed.connect(self._on_create)
        self.email.returnPressed.connect(self._on_create)
        self.password.returnPressed.connect(self._on_create)
        self.password2.returnPressed.connect(self._on_create)

    @QtCore.Slot()
    def _on_create(self):
        self.error.setText("")
        username = self.username.text().strip()
        email = self.email.text().strip()
        password = self.password.text()
        password2 = self.password2.text()

        if not username or not email or not password:
            self.error.setText("Please enter username, email, and password.")
            return
        if password != password2:
            self.error.setText("Passwords do not match.")
            return

        self.btn_create.setEnabled(False)
        result = self.api.register(username=username, email=email, password=password)
        self.btn_create.setEnabled(True)

        if result.ok:
            self.accept()
        else:
            self.error.setText(result.message or "Registration failed")


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

        self.btn_register = QtWidgets.QPushButton("Create account")
        self.btn_register.setFlat(True)
        self.btn_register.clicked.connect(self._on_register)

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
        layout.addWidget(self.btn_register)

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

    @QtCore.Slot()
    def _on_register(self):
        dlg = RegisterDialog(self.api, parent=self)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        # Auto-login after successful registration
        self.username.setText(dlg.username.text().strip())
        self.password.setText(dlg.password.text())
        self._on_login()
