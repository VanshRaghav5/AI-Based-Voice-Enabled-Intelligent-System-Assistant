from __future__ import annotations
from typing import Any, Dict

from PySide6 import QtCore, QtWidgets


class _InfoCard(QtWidgets.QFrame):
    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background: #1f2937; border: 1px solid #374151; border-radius: 10px; }"
            "QLabel { color: #e5e7eb; }"
        )
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        title_lbl = QtWidgets.QLabel(title)
        title_lbl.setStyleSheet("color: #9ca3af; font-size: 12px; font-weight: 600;")
        value_lbl = QtWidgets.QLabel(value)
        value_lbl.setStyleSheet("font-size: 14px; font-weight: 600;")
        value_lbl.setWordWrap(True)

        lay.addWidget(title_lbl)
        lay.addWidget(value_lbl)

class ProfileDialog(QtWidgets.QDialog):
    def __init__(self, api_client, session_store, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.session = session_store
        self._profile_payload: Dict[str, Any] = {}

        self.setWindowTitle("User Profile")
        self.setMinimumSize(720, 520)
        self.setStyleSheet("""
            QDialog {
                background: #161b22;
                border-radius: 12px;
                border: 1px solid #374151;
            }
            QLabel { color: #e5e7eb; font-family: 'Segoe UI', Arial; }
            QPushButton {
                background: #1f2937; color: white; padding: 10px 12px; border-radius: 8px; border: 1px solid #374151; font-weight: 600; text-align: left;
            }
            QPushButton:hover { background: #374151; border: 1px solid #4b5563; }
            QLineEdit, QComboBox {
                background: #111827;
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 8px;
            }
            QCheckBox { color: #e5e7eb; }
        """)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        header = QtWidgets.QHBoxLayout()
        self.avatar = QtWidgets.QLabel("U")
        self.avatar.setFixedSize(48, 48)
        self.avatar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("background: #3b82f6; color: white; border-radius: 24px; font-size: 20px; font-weight: 700;")

        self.lbl_name = QtWidgets.QLabel("User")
        self.lbl_name.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.lbl_sub = QtWidgets.QLabel("Personalization")
        self.lbl_sub.setStyleSheet("color: #9ca3af; font-size: 12px;")
        name_box = QtWidgets.QVBoxLayout()
        name_box.setSpacing(2)
        name_box.addWidget(self.lbl_name)
        name_box.addWidget(self.lbl_sub)

        header.addWidget(self.avatar)
        header.addSpacing(10)
        header.addLayout(name_box)
        header.addStretch()

        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.load_profile)
        self.btn_refresh.setFixedWidth(90)
        header.addWidget(self.btn_refresh)

        root.addLayout(header)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(12)

        self.nav = QtWidgets.QListWidget()
        self.nav.setFixedWidth(190)
        self.nav.addItems(["Profile", "Preferences", "Memory", "Connected Apps"])
        self.nav.setCurrentRow(0)
        self.nav.setStyleSheet(
            "QListWidget { background: #111827; border: 1px solid #374151; border-radius: 10px; padding: 6px; }"
            "QListWidget::item { padding: 10px; border-radius: 8px; }"
            "QListWidget::item:selected { background: #1f2937; color: #ffffff; font-weight: 700; }"
        )
        self.nav.currentRowChanged.connect(self._switch_page)

        self.stack = QtWidgets.QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: #0f141b; border: 1px solid #1f2937; border-radius: 10px; }")

        self.page_profile = QtWidgets.QWidget()
        self.page_preferences = QtWidgets.QWidget()
        self.page_memory = QtWidgets.QWidget()
        self.page_apps = QtWidgets.QWidget()
        self.stack.addWidget(self.page_profile)
        self.stack.addWidget(self.page_preferences)
        self.stack.addWidget(self.page_memory)
        self.stack.addWidget(self.page_apps)

        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

        self._build_profile_page()
        self._build_preferences_page()
        self._build_memory_page()
        self._build_apps_page()

        footer = QtWidgets.QHBoxLayout()
        footer.addStretch(1)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet("QPushButton { background: #ef4444; border: none; text-align: center; }")
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)
        root.addLayout(footer)

        self.load_profile()

    def _switch_page(self, idx: int):
        if 0 <= idx < self.stack.count():
            self.stack.setCurrentIndex(idx)

    def _build_profile_page(self):
        lay = QtWidgets.QVBoxLayout(self.page_profile)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        self.profile_content = QtWidgets.QVBoxLayout()
        self.profile_content.setSpacing(10)
        lay.addLayout(self.profile_content)
        lay.addStretch(1)

    def _build_preferences_page(self):
        lay = QtWidgets.QVBoxLayout(self.page_preferences)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        self.pref_persona = QtWidgets.QComboBox()
        self.pref_persona.addItems(["default", "butler", "developer", "sarcastic", "friendly", "professional", "concise"])
        self.pref_language = QtWidgets.QComboBox()
        self.pref_language.addItems(["en", "hi", "hinglish", "es", "fr"])
        self.pref_timezone = QtWidgets.QLineEdit()
        self.pref_primary_email = QtWidgets.QLineEdit()
        self.pref_memory_enabled = QtWidgets.QCheckBox("Enable assistant memory")

        lay.addWidget(QtWidgets.QLabel("Persona"))
        lay.addWidget(self.pref_persona)
        lay.addWidget(QtWidgets.QLabel("Language"))
        lay.addWidget(self.pref_language)
        lay.addWidget(QtWidgets.QLabel("Timezone"))
        lay.addWidget(self.pref_timezone)
        lay.addWidget(QtWidgets.QLabel("Primary Email"))
        lay.addWidget(self.pref_primary_email)
        lay.addWidget(self.pref_memory_enabled)

        btn_save = QtWidgets.QPushButton("Save Preferences")
        btn_save.clicked.connect(self._save_preferences)
        lay.addWidget(btn_save)
        lay.addStretch(1)

    def _build_memory_page(self):
        lay = QtWidgets.QVBoxLayout(self.page_memory)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        self.memory_name = QtWidgets.QLabel("Name: -")
        self.memory_tz = QtWidgets.QLabel("Timezone: -")
        self.memory_email = QtWidgets.QLabel("Primary Email: -")
        for w in [self.memory_name, self.memory_tz, self.memory_email]:
            w.setStyleSheet("font-size: 14px; color: #e5e7eb;")
            lay.addWidget(w)

        sample = QtWidgets.QLabel("Sure <name>, I'll send the email.")
        sample.setStyleSheet("color: #93c5fd; font-style: italic; margin-top: 8px;")
        lay.addWidget(sample)
        lay.addStretch(1)

    def _build_apps_page(self):
        lay = QtWidgets.QVBoxLayout(self.page_apps)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)
        self.apps_content = QtWidgets.QVBoxLayout()
        self.apps_content.setSpacing(10)
        lay.addLayout(self.apps_content)
        lay.addStretch(1)

    def load_profile(self):
        ok, payload = self.api.get_profile()
        if not ok:
            # Fallback to session + settings for partial dynamic behavior.
            user = self.session.user or {}
            ok_settings, settings = self.api.get_settings()
            settings = settings if ok_settings else {}
            payload = {
                "profile": {
                    "name": user.get("username", "User"),
                    "email": user.get("email", ""),
                    "role": user.get("role", "user"),
                },
                "preferences": settings,
                "memory": {
                    "name": user.get("username", "User"),
                    "timezone": settings.get("timezone", "IST"),
                    "primary_email": settings.get("primary_email") or user.get("email", ""),
                },
                "connected_apps": [],
            }

        self._profile_payload = payload or {}
        self._render_payload()

    def _render_payload(self):
        profile = self._profile_payload.get("profile", {})
        prefs = self._profile_payload.get("preferences", {})
        memory = self._profile_payload.get("memory", {})
        apps = self._profile_payload.get("connected_apps", [])

        name = str(profile.get("name") or "User")
        self.lbl_name.setText(name)
        self.lbl_sub.setText(f"{profile.get('email', '')} | role: {profile.get('role', 'user')}")
        self.avatar.setText(name[:1].upper())

        while self.profile_content.count():
            item = self.profile_content.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.profile_content.addWidget(_InfoCard("Name", name))
        self.profile_content.addWidget(_InfoCard("Primary Email", str(memory.get("primary_email") or profile.get("email") or "-")))
        self.profile_content.addWidget(_InfoCard("Timezone", str(memory.get("timezone") or "IST")))

        self.pref_persona.setCurrentText(str(prefs.get("persona", "default")))
        self.pref_language.setCurrentText(str(prefs.get("language", "en")))
        self.pref_timezone.setText(str(prefs.get("timezone", memory.get("timezone", "IST"))))
        self.pref_primary_email.setText(str(prefs.get("primary_email", memory.get("primary_email", profile.get("email", "")))))
        self.pref_memory_enabled.setChecked(bool(prefs.get("memory_enabled", True)))

        self.memory_name.setText(f"Name: {memory.get('name', name)}")
        self.memory_tz.setText(f"Timezone: {memory.get('timezone', 'IST')}")
        self.memory_email.setText(f"Primary Email: {memory.get('primary_email', profile.get('email', ''))}")

        while self.apps_content.count():
            item = self.apps_content.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not apps:
            self.apps_content.addWidget(_InfoCard("Connected Apps", "No app integrations reported by backend yet."))
        else:
            for app in apps:
                status = str(app.get("status", "unknown")).replace("_", " ").title()
                details = app.get("details", "")
                text = f"Status: {status}"
                if details:
                    text += f"\n{details}"
                self.apps_content.addWidget(_InfoCard(str(app.get("name", "App")), text))

    def _save_preferences(self):
        payload = {
            "persona": self.pref_persona.currentText(),
            "language": self.pref_language.currentText(),
            "memory_enabled": bool(self.pref_memory_enabled.isChecked()),
            "timezone": self.pref_timezone.text().strip() or "IST",
            "primary_email": self.pref_primary_email.text().strip(),
        }
        result = self.api.update_settings(payload)
        if result.ok:
            QtWidgets.QMessageBox.information(self, "Preferences", "Preferences saved.")
            self.load_profile()
            return

        QtWidgets.QMessageBox.warning(
            self,
            "Preferences",
            result.message or "Unable to save preferences. Ensure this account has permission.",
        )

        # Header
        header_layout = QtWidgets.QHBoxLayout()
        avatar = QtWidgets.QLabel("U")
        avatar.setFixedSize(56, 56)
        avatar.setStyleSheet("background: #3b82f6; color: white; border-radius: 28px; font-size: 24px; font-weight: bold;")
        avatar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(2)
        name_lbl = QtWidgets.QLabel("Uday")
        name_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        email_lbl = QtWidgets.QLabel("bansaluday112@gmail.com")
        email_lbl.setStyleSheet("color: #9ca3af; font-size: 13px;")
        tz_lbl = QtWidgets.QLabel("Timezone: IST")
        tz_lbl.setStyleSheet("color: #9ca3af; font-size: 13px;")
        
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(email_lbl)
        info_layout.addWidget(tz_lbl)
        
        header_layout.addWidget(avatar)
        header_layout.addSpacing(16)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        layout.addLayout(header_layout)
        
        # Divider
        divider = QtWidgets.QFrame()
        divider.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        divider.setStyleSheet("background: #374151;")
        layout.addWidget(divider)
        
        # Menu Options
        options = [
            "👤   Profile Details",
            "⚙   Preferences",
            "🧠   Assistant Context Memory",
            "🔌   Connected Apps"
        ]
        
        for opt in options:
            btn = QtWidgets.QPushButton(opt)
            btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)
            
        layout.addStretch()
        
        # Close Button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setStyleSheet("background: #ef4444; border: none; text-align: center;")
        close_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
