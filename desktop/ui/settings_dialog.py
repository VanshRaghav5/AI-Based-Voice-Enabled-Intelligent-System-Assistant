from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OmniAssist Settings")
        self.setMinimumWidth(300)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        layout = QtWidgets.QVBoxLayout(self)

        # Persona Section
        layout.addWidget(QtWidgets.QLabel("<b>Assistant Persona</b>"))
        self.cb_persona = QtWidgets.QComboBox()
        self.cb_persona.addItems(["Default", "Butler", "Developer", "Sarcastic"])
        self.cb_persona.setStyleSheet("background: #2b2b2b; color: white; padding: 5px; border-radius: 4px;")
        layout.addWidget(self.cb_persona)

        layout.addSpacing(10)

        # Theme Section
        layout.addWidget(QtWidgets.QLabel("<b>Theme</b>"))
        self.cb_theme = QtWidgets.QComboBox()
        self.cb_theme.addItems(["Dark (Default)", "Light"])
        self.cb_theme.setStyleSheet("background: #2b2b2b; color: white; padding: 5px; border-radius: 4px;")
        layout.addWidget(self.cb_theme)
        
        layout.addStretch()

        # Action Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_signout = QtWidgets.QPushButton("Sign Out")
        self.btn_signout.setStyleSheet("background: #ef4444; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        
        self.btn_close = QtWidgets.QPushButton("Done")
        self.btn_close.setStyleSheet("background: #3b82f6; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")

        btn_layout.addWidget(self.btn_signout)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)

        self.btn_close.clicked.connect(self.accept)

        # Setup standard response flow if they click sign out
        self.signout_requested = False
        self.btn_signout.clicked.connect(self._on_signout)
        
    def _on_signout(self):
        reply = QtWidgets.QMessageBox.question(
            self, "Sign Out", "Are you sure you want to sign out?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.signout_requested = True
            self.accept()
