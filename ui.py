from __future__ import annotations

import json
import math
import os
import platform
import random
import sys
import threading
import time
from collections import deque
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

# Import security for authentication
try:
    from security import get_auth_manager, authenticate_user
    _SECURITY_AVAILABLE = True
except ImportError:
    _SECURITY_AVAILABLE = False


def get_base_dir() -> Path:
	if getattr(sys, "frozen", False):
		return Path(sys.executable).parent
	return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE = CONFIG_DIR / "api_keys.json"

SYSTEM_NAME = "O.M.I.N.I"
MODEL_BADGE = "V2.0"

C_BG = "#000000"
C_PRI = "#00d4ff"
C_MID = "#007a99"
C_DIM = "#003344"
C_DIMMER = "#001520"
C_ACC = "#ff6600"
C_ACC2 = "#ffcc00"
C_TEXT = "#8ffcff"
C_PANEL = "#010c10"
C_GREEN = "#00ff88"
C_RED = "#ff3333"
C_MUTED = "#ff3366"

# ═══════════════════════════════════════════════════════════════════════════════
# THEMES - Multiple color schemes for UI customization
# ═══════════════════════════════════════════════════════════════════════
THEMES = {
    "default": {
        "primary": "#00d4ff", "accent": "#ff6600", "glow": "#00d4ff",
        "secondary": "#007a99", "dim": "#003344", "bg": "#010c10"
    },
    "red": {
        "primary": "#ff4400", "accent": "#ff8800", "glow": "#ff4400",
        "secondary": "#992200", "dim": "#441100", "bg": "#100800"
    },
    "purple": {
        "primary": "#cc00ff", "accent": "#ff00cc", "glow": "#cc00ff",
        "secondary": "#770099", "dim": "#330044", "bg": "#100810"
    },
    "matrix": {
        "primary": "#00ff00", "accent": "#88ff00", "glow": "#00ff00",
        "secondary": "#009900", "dim": "#003300", "bg": "#000800"
    },
}

_current_theme = "default"
_animation_intensity = 1.0
_sound_enabled = False
_screen_shake_offset = (0, 0)
_click_ripples: list[tuple[int, int, float]] = []
_hover_highlights: list[tuple[int, int, int, int]] = []


class LoginScreen(QtWidgets.QWidget):
    """Login screen for authentication."""

    login_success = QtCore.Signal(str, str)  # username, password

    def __init__(self):
        # Create QApplication first
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)

        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(420, 420)
        self.setWindowTitle("OMINI - Login")
        self.setStyleSheet(f"background: {C_BG};")

        # Main container with border
        container = QtWidgets.QWidget()
        container.setObjectName("container")
        container.setStyleSheet(f"""
            QWidget#container {{
                background: {C_PANEL};
                border: 2px solid {C_PRI};
                border-radius: 15px;
            }}
        """)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)
        container.setLayout(main_layout)
        self.setLayout(main_layout)
        main_layout.addWidget(container)

        # Title with glow effect - reduced size
        title = QtWidgets.QLabel("O M I N I")
        title.setStyleSheet("""
            color: #00d4ff;
            font-size: 28px;
            font-weight: bold;
            letter-spacing: 6px;
            padding: 5px;
        """)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setMinimumHeight(40)
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QtWidgets.QLabel("Sign in to continue")
        subtitle.setStyleSheet("""
            color: #8ffcff;
            font-size: 12px;
            padding-bottom: 8px;
        """)
        subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Username field
        self.username_edit = QtWidgets.QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        self.username_edit.setStyleSheet("""
            QLineEdit {
                background: #0a1a1a;
                color: #ffffff;
                border: 1px solid #005566;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00d4ff;
                background: #0f2020;
            }
            QLineEdit::placeholder {
                color: #406066;
            }
        """)
        self.username_edit.setMinimumHeight(45)
        main_layout.addWidget(self.username_edit)

        # Password field
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                background: #0a1a1a;
                color: #ffffff;
                border: 1px solid #005566;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00d4ff;
                background: #0f2020;
            }
            QLineEdit::placeholder {
                color: #406066;
            }
        """)
        self.password_edit.setMinimumHeight(45)
        self.password_edit.returnPressed.connect(self._do_login)
        main_layout.addWidget(self.password_edit)

        # Error label
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("""
            color: #ff4444;
            font-size: 12px;
            padding: 5px;
        """)
        self.error_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.error_label)

        # Login button
        self.login_btn = QtWidgets.QPushButton("SIGN IN")
        self.login_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00a0cc, stop:1 #00d4ff);
                color: #000000;
                border: none;
                border-radius: 8px;
                padding: 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00c0ee, stop:1 #00eeff);
            }
            QPushButton:pressed {
                background: #0088aa;
            }
        """)
        self.login_btn.setMinimumHeight(45)
        self.login_btn.clicked.connect(self._do_login)
        main_layout.addWidget(self.login_btn)

        # Guest button
        guest_btn = QtWidgets.QPushButton("Continue as Guest")
        guest_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        guest_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8ffcff;
                border: 1px solid #005566;
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                border: 1px solid #00d4ff;
                color: #00d4ff;
            }
        """)
        guest_btn.setMinimumHeight(40)
        guest_btn.clicked.connect(self._login_guest)
        main_layout.addWidget(guest_btn)

        # Version label
        ver = QtWidgets.QLabel("v2.0")
        ver.setStyleSheet("""
            color: #304455;
            font-size: 10px;
            padding-top: 10px;
        """)
        ver.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(ver)

    def _do_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            self.error_label.setText("Please enter username and password")
            return

        if _SECURITY_AVAILABLE:
            success, msg = authenticate_user(username, password)
            if success:
                self.login_success.emit(username, password)
            else:
                self.error_label.setText(msg)
        else:
            # No security module - allow login
            self.login_success.emit(username, password)

    def _login_guest(self):
        self.login_success.emit("guest", "")


class OminiUI(QtWidgets.QWidget):
	log_requested = QtCore.Signal(str)
	state_requested = QtCore.Signal(str)

	def __init__(self, face_path: str, size: tuple[int, int] | None = None):
		app = QtWidgets.QApplication.instance()
		if app is None:
			# Fix DPI awareness warning on Windows
			try:
				import ctypes
				ctypes.windll.shcore.SetProcessDpiAwarenessContext(2)  # Per-Monitor V2
			except Exception:
				pass
			self._app = QtWidgets.QApplication(sys.argv)
		else:
			self._app = app

		super().__init__()
		self.setWindowTitle("OMINI ASSISTANT")
		self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowMaximizeButtonHint)

		screen = QtGui.QGuiApplication.primaryScreen()
		sg = screen.availableGeometry() if screen else QtCore.QRect(0, 0, 1366, 768)
		width = min(sg.width(), 984)
		height = min(sg.height(), 816)
		if size is not None:
			width, height = size
		self.resize(width, height)
		self.setMinimumSize(width, height)
		self.setMaximumSize(width, height)
		self._center_on_screen(sg)

		self.W = width
		self.H = height
		self.FACE_SZ = min(int(self.H * 0.54), 400)
		self.FCX = self.W // 2
		self.FCY = int(self.H * 0.13) + self.FACE_SZ // 2

		self.speaking = False
		self.muted = False
		self.scale = 1.0
		self.target_scale = 1.0
		self.halo_a = 60.0
		self.target_halo = 60.0
		self.last_t = time.time()
		self.tick = 0
		self.scan_angle = 0.0
		self.scan2_angle = 180.0
		self.rings_spin = [0.0, 120.0, 240.0]
		self.pulse_r = [0.0, self.FACE_SZ * 0.26, self.FACE_SZ * 0.52]
		self.status_text = "INITIALISING"
		self.status_blink = True
		self._omini_state = "INITIALISING"

		self.typing_queue: deque[str] = deque()
		self.is_typing = False
		self._typing_text = ""
		self._typing_idx = 0
		self._typing_color = QtGui.QColor(C_TEXT)

		self.on_text_command = None
		self._api_key_ready = False

		self._face_pixmap: QtGui.QPixmap | None = None
		self._has_face = False
		self._load_face(face_path)

		# ═══════════════════════════════════════════════════════════════════════
		# Advanced UI Features
		# ═══════════════════════════════════════════════════════════════════════
		self._mouse_pos = (self.W // 2, self.H // 2)
		self._orb_offset = (0, 0)
		self._data_stream_chars = []
		self._energy_pulse = 0.0
		self._prev_state = ""
		self._status_color = QtGui.QColor(C_GREEN)
		self._status_color_target = QtGui.QColor(C_GREEN)
		self._start_time = time.time()
		self._messages_sent = 0
		self._screen_shake = 0

		self.setAutoFillBackground(True)
		pal = self.palette()
		pal.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(C_BG))
		self.setPalette(pal)

		self._build_overlay_widgets()
		QtGui.QShortcut(QtGui.QKeySequence("F4"), self, activated=self._toggle_mute)

		self.log_requested.connect(self._enqueue_log)
		self.state_requested.connect(self._set_state_impl)

		self._api_key_ready = self._api_keys_exist()
		if not self._api_key_ready:
			QtCore.QTimer.singleShot(10, self._show_setup_ui)

		self._anim_timer = QtCore.QTimer(self)
		self._anim_timer.timeout.connect(self._animate)
		self._anim_timer.start(16)
		self.setMouseTracking(True)

	def run(self) -> int:
		self.show()
		return self._app.exec()

	def _center_on_screen(self, sg: QtCore.QRect) -> None:
		geo = self.frameGeometry()
		geo.moveCenter(sg.center())
		self.move(geo.topLeft())

	def _build_overlay_widgets(self) -> None:
		lw = int(self.W * 0.72)
		lh = 110
		log_y = self.H - lh - 80

		self.log_frame = QtWidgets.QFrame(self)
		self.log_frame.setGeometry((self.W - lw) // 2, log_y, lw, lh)
		self.log_frame.setStyleSheet(
			"QFrame {"
			f"background:{C_PANEL};"
			f"border:1px solid {C_MID};"
			"}"
		)

		self.log_text = QtWidgets.QTextEdit(self.log_frame)
		self.log_text.setGeometry(0, 0, lw, lh)
		self.log_text.setReadOnly(True)
		self.log_text.setStyleSheet(
			"QTextEdit {"
			f"color:{C_TEXT};"
			f"background:{C_PANEL};"
			"border:0;"
			"font-family:'Courier New';"
			"font-size:10pt;"
			"padding:6px 10px;"
			"}"
		)

		input_y = log_y + lh + 6
		btn_w = 70
		inp_w = lw - btn_w - 4
		x0 = (self.W - lw) // 2

		self._input = QtWidgets.QLineEdit(self)
		self._input.setGeometry(x0, input_y, inp_w, 28)
		self._input.setStyleSheet(
			"QLineEdit {"
			f"color:{C_TEXT};"
			"background:#000d12;"
			"border:1px solid #003344;"
			"padding-left:6px;"
			"font-family:'Courier New';"
			"font-size:10pt;"
			"}"
			"QLineEdit:focus { border:1px solid #00d4ff; }"
		)
		self._input.returnPressed.connect(self._on_input_submit)

		self._send_btn = QtWidgets.QPushButton("SEND >", self)
		self._send_btn.setGeometry(x0 + inp_w + 4, input_y, btn_w, 28)
		self._send_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
		self._send_btn.clicked.connect(self._on_input_submit)
		self._send_btn.setStyleSheet(
			"QPushButton {"
			f"color:{C_PRI};"
			f"background:{C_PANEL};"
			f"border:1px solid {C_MID};"
			"font-family:'Courier New';"
			"font-size:9pt;"
			"font-weight:700;"
			"}"
			"QPushButton:hover {"
			"background:#003344;"
			"color:#000000;"
			"}"
		)

		self._mute_btn = QtWidgets.QPushButton(self)
		self._mute_btn.setGeometry(18, self.H - 70, 110, 32)
		self._mute_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
		self._mute_btn.clicked.connect(self._toggle_mute)
		self._draw_mute_button()

	def _draw_mute_button(self) -> None:
		if self.muted:
			border = C_MUTED
			fill = "#1a0008"
			icon = "MUTED"
			fg = C_MUTED
		else:
			border = C_MID
			fill = C_PANEL
			icon = "LIVE"
			fg = C_GREEN
		self._mute_btn.setText(icon)
		self._mute_btn.setStyleSheet(
			"QPushButton {"
			f"color:{fg};"
			f"background:{fill};"
			f"border:1px solid {border};"
			"font-family:'Courier New';"
			"font-size:10pt;"
			"font-weight:700;"
			"}"
		)

	def _toggle_mute(self) -> None:
		self.muted = not self.muted
		self._draw_mute_button()
		if self.muted:
			self.set_state("MUTED")
			self.write_log("SYS: Microphone muted.")
		else:
			self.set_state("LISTENING")
			self.write_log("SYS: Microphone active.")

	def _on_input_submit(self) -> None:
		text = self._input.text().strip()
		if not text:
			return
		self._input.clear()
		self.write_log(f"You: {text}")
		if self.on_text_command:
			threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

	def set_state(self, state: str) -> None:
		self.state_requested.emit(state)

	def _set_state_impl(self, state: str) -> None:
		# Energy pulse on state transition
		if state != self._prev_state and self._prev_state:
			self._energy_pulse = 20 * _animation_intensity
		self._prev_state = self._omini_state

		self._omini_state = state
		if state == "MUTED":
			self.status_text = "MUTED"
			self.speaking = False
			self._status_color = QtGui.QColor(C_MUTED)
		elif state == "SPEAKING":
			self.status_text = "SPEAKING"
			self.speaking = True
			self._status_color = QtGui.QColor(C_ACC)
		elif state == "THINKING":
			self.status_text = "THINKING"
			self.speaking = False
			self._status_color = QtGui.QColor(C_ACC2)
		elif state == "LISTENING":
			self.status_text = "LISTENING"
			self.speaking = False
			self._status_color = QtGui.QColor(C_GREEN)
		elif state == "PROCESSING":
			self.status_text = "PROCESSING"
			self.speaking = False
			self._status_color = QtGui.QColor(C_ACC2)
		else:
			self.status_text = "ONLINE"
			self.speaking = False
			self._status_color = QtGui.QColor(C_PRI)
		self.update()

	def _load_face(self, path: str) -> None:
		p = Path(path)
		if not p.exists():
			self._has_face = False
			return
		pix = QtGui.QPixmap(str(p))
		if pix.isNull():
			self._has_face = False
			return
		self._face_pixmap = pix
		self._has_face = True

	@staticmethod
	def _ac(r: int, g: int, b: int, a: int) -> QtGui.QColor:
		c = QtGui.QColor(r, g, b)
		c.setAlpha(max(0, min(255, a)))
		return c

	def _animate(self) -> None:
		self.tick += 1
		now = time.time()

		if now - self.last_t > (0.14 if self.speaking else 0.55):
			if self.speaking:
				self.target_scale = random.uniform(1.05, 1.11)
				self.target_halo = random.uniform(138, 182)
			elif self.muted:
				self.target_scale = random.uniform(0.998, 1.001)
				self.target_halo = random.uniform(20, 32)
			else:
				self.target_scale = random.uniform(1.001, 1.007)
				self.target_halo = random.uniform(50, 68)
			self.last_t = now

		sp = 0.35 if self.speaking else 0.16
		self.scale += (self.target_scale - self.scale) * sp
		self.halo_a += (self.target_halo - self.halo_a) * sp

		speeds = [1.2, -0.8, 1.9] if self.speaking else [0.5, -0.3, 0.82]
		for i, s in enumerate(speeds):
			self.rings_spin[i] = (self.rings_spin[i] + s) % 360

		self.scan_angle = (self.scan_angle + (2.8 if self.speaking else 1.2)) % 360
		self.scan2_angle = (self.scan2_angle + (-1.7 if self.speaking else -0.68)) % 360

		pspd = 3.8 if self.speaking else 1.8
		limit = self.FACE_SZ * 0.72
		new_p = [r + pspd for r in self.pulse_r if r + pspd < limit]
		if len(new_p) < 3 and random.random() < (0.06 if self.speaking else 0.022):
			new_p.append(0.0)
		self.pulse_r = new_p

		if self.tick % 40 == 0:
			self.status_blink = not self.status_blink

		self.update()

	def paintEvent(self, event: QtGui.QPaintEvent) -> None:
		_ = event
		p = QtGui.QPainter(self)
		p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
		p.fillRect(self.rect(), QtGui.QColor(C_BG))

		w, h = self.W, self.H
		fcx, fcy, fw = self.FCX, self.FCY, self.FACE_SZ

		grid_pen = QtGui.QPen(QtGui.QColor(C_DIMMER))
		grid_pen.setWidth(1)
		p.setPen(grid_pen)
		for x in range(0, w, 44):
			for y in range(0, h, 44):
				p.drawPoint(x, y)

		for r in range(int(fw * 0.54), int(fw * 0.28), -22):
			frac = 1.0 - (r - fw * 0.28) / (fw * 0.26)
			ga = max(0, min(255, int(self.halo_a * 0.09 * frac)))
			col = self._ac(255, 0, 17, ga) if self.muted else self._ac(0, 212, 255, ga)
			pen = QtGui.QPen(col, 2)
			p.setPen(pen)
			p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
			p.drawEllipse(QtCore.QPoint(fcx, fcy), r, r)

		for pr in self.pulse_r:
			pa = max(0, int(220 * (1.0 - pr / (fw * 0.72))))
			r = int(pr)
			col = self._ac(255, 30, 80, pa // 3) if self.muted else self._ac(0, 212, 255, pa)
			p.setPen(QtGui.QPen(col, 2))
			p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
			p.drawEllipse(QtCore.QPoint(fcx, fcy), r, r)

		rings = [(0.47, 3, 110, 75), (0.39, 2, 75, 55), (0.31, 1, 55, 38)]
		for idx, (r_frac, w_ring, arc_l, gap) in enumerate(rings):
			ring_r = int(fw * r_frac)
			base_a = self.rings_spin[idx]
			a_val = max(0, min(255, int(self.halo_a * (1.0 - idx * 0.18))))
			col = self._ac(255, 30, 80, a_val) if self.muted else self._ac(0, 212, 255, a_val)
			p.setPen(QtGui.QPen(col, w_ring))
			rect = QtCore.QRectF(fcx - ring_r, fcy - ring_r, ring_r * 2, ring_r * 2)
			for s in range(360 // (arc_l + gap)):
				start = (base_a + s * (arc_l + gap)) % 360
				p.drawArc(rect, int(-start * 16), int(-arc_l * 16))

		sr = int(fw * 0.49)
		scan_a = min(255, int(self.halo_a * 1.4))
		arc_ext = 70 if self.speaking else 42
		scan_col = self._ac(255, 30, 80, scan_a) if self.muted else self._ac(0, 212, 255, scan_a)
		rect = QtCore.QRectF(fcx - sr, fcy - sr, sr * 2, sr * 2)
		p.setPen(QtGui.QPen(scan_col, 3))
		p.drawArc(rect, int(-self.scan_angle * 16), int(-arc_ext * 16))
		p.setPen(QtGui.QPen(self._ac(255, 100, 0, scan_a // 2), 2))
		p.drawArc(rect, int(-self.scan2_angle * 16), int(-arc_ext * 16))

		t_out = int(fw * 0.495)
		t_in = int(fw * 0.472)
		p.setPen(QtGui.QPen(self._ac(0, 212, 255, 155), 1))
		for deg in range(0, 360, 10):
			rad = math.radians(deg)
			inn = t_in if deg % 30 == 0 else t_in + 5
			p.drawLine(
				QtCore.QPointF(fcx + t_out * math.cos(rad), fcy - t_out * math.sin(rad)),
				QtCore.QPointF(fcx + inn * math.cos(rad), fcy - inn * math.sin(rad)),
			)

		ch_r = int(fw * 0.50)
		gap = int(fw * 0.15)
		p.setPen(QtGui.QPen(self._ac(0, 212, 255, int(self.halo_a * 0.55)), 1))
		p.drawLine(fcx - ch_r, fcy, fcx - gap, fcy)
		p.drawLine(fcx + gap, fcy, fcx + ch_r, fcy)
		p.drawLine(fcx, fcy - ch_r, fcx, fcy - gap)
		p.drawLine(fcx, fcy + gap, fcx, fcy + ch_r)

		blen = 22
		p.setPen(QtGui.QPen(self._ac(0, 212, 255, 200), 2))
		hl, hr = fcx - fw // 2, fcx + fw // 2
		ht, hb = fcy - fw // 2, fcy + fw // 2
		corners = [(hl, ht, 1, 1), (hr, ht, -1, 1), (hl, hb, 1, -1), (hr, hb, -1, -1)]
		for bx, by, sdx, sdy in corners:
			p.drawLine(bx, by, bx + sdx * blen, by)
			p.drawLine(bx, by, bx, by + sdy * blen)

		if self._has_face and self._face_pixmap is not None:
			draw_w = int(fw * self.scale)
			rect = QtCore.QRect(fcx - draw_w // 2, fcy - draw_w // 2, draw_w, draw_w)
			p.save()
			clip = QtGui.QPainterPath()
			clip.addEllipse(QtCore.QRectF(rect))
			p.setClipPath(clip)
			p.drawPixmap(rect, self._face_pixmap)
			p.restore()
		else:
			orb_r = int(fw * 0.27 * self.scale)
			orb_color = (255, 30, 80) if self.muted else (0, 65, 120)
			p.setPen(QtCore.Qt.PenStyle.NoPen)
			for i in range(7, 0, -1):
				r2 = int(orb_r * i / 7)
				frac = i / 7
				ga = max(0, min(255, int(self.halo_a * 1.1 * frac)))
				p.setBrush(self._ac(int(orb_color[0] * frac), int(orb_color[1] * frac), int(orb_color[2] * frac), ga))
				p.drawEllipse(QtCore.QPoint(fcx, fcy), r2, r2)
			p.setPen(self._ac(0, 212, 255, min(255, int(self.halo_a * 2))))
			f = QtGui.QFont("Courier New", 14)
			f.setBold(True)
			p.setFont(f)
			p.drawText(QtCore.QRect(0, fcy - 15, w, 30), QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)

		hdr = 62
		p.fillRect(0, 0, w, hdr, QtGui.QColor("#00080d"))
		p.setPen(QtGui.QPen(QtGui.QColor(C_MID), 1))
		p.drawLine(0, hdr, w, hdr)

		title_font = QtGui.QFont("Courier New", 18)
		title_font.setBold(True)
		p.setFont(title_font)
		p.setPen(QtGui.QColor(C_PRI))
		p.drawText(QtCore.QRect(0, 8, w, 28), QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)

		sub_font = QtGui.QFont("Courier New", 9)
		p.setFont(sub_font)
		p.setPen(QtGui.QColor(C_MID))
		p.drawText(QtCore.QRect(0, 34, w, 20), QtCore.Qt.AlignmentFlag.AlignHCenter, "Just A Rather Very Intelligent System")

		p.setPen(QtGui.QColor(C_DIM))
		p.drawText(16, 31, MODEL_BADGE)

		clock_font = QtGui.QFont("Courier New", 14)
		clock_font.setBold(True)
		p.setFont(clock_font)
		p.setPen(QtGui.QColor(C_PRI))
		p.drawText(QtCore.QRect(0, 10, w - 16, 40), QtCore.Qt.AlignmentFlag.AlignRight, time.strftime("%H:%M:%S"))

		sy = fcy + fw // 2 + 45
		p.setFont(QtGui.QFont("Courier New", 11, QtGui.QFont.Weight.Bold))
		if self.muted:
			stat = "MUTED"
			sc = QtGui.QColor(C_MUTED)
		elif self.speaking:
			stat = "SPEAKING"
			sc = QtGui.QColor(C_ACC)
		elif self._omini_state == "THINKING":
			stat = f"{'◈' if self.status_blink else '◇'} THINKING"
			sc = QtGui.QColor(C_ACC2)
		elif self._omini_state == "PROCESSING":
			stat = f"{'▷' if self.status_blink else '▶'} PROCESSING"
			sc = QtGui.QColor(C_ACC2)
		elif self._omini_state == "LISTENING":
			stat = f"{'●' if self.status_blink else '○'} LISTENING"
			sc = QtGui.QColor(C_GREEN)
		else:
			stat = f"{'●' if self.status_blink else '○'} {self.status_text}"
			sc = QtGui.QColor(C_PRI)
		p.setPen(sc)
		p.drawText(QtCore.QRect(0, sy - 12, w, 24), QtCore.Qt.AlignmentFlag.AlignHCenter, stat)

		wy = sy + 22
		n = 32
		bh = 18
		bw = 8
		total_w = n * bw
		wx0 = (w - total_w) // 2
		p.setPen(QtCore.Qt.PenStyle.NoPen)
		for i in range(n):
			if self.muted:
				hb2 = 2
				col = QtGui.QColor(C_MUTED)
			elif self.speaking:
				hb2 = random.randint(3, bh)
				col = QtGui.QColor(C_PRI if hb2 > bh * 0.6 else C_MID)
			else:
				hb2 = int(3 + 2 * math.sin(self.tick * 0.08 + i * 0.55))
				col = QtGui.QColor(C_DIM)
			bx = wx0 + i * bw
			p.setBrush(col)
			p.drawRect(bx, wy + bh - hb2, bw - 1, hb2)

		p.fillRect(0, h - 28, w, 28, QtGui.QColor("#00080d"))
		p.setPen(QtGui.QPen(QtGui.QColor(C_DIM), 1))
		p.drawLine(0, h - 28, w, h - 28)
		p.setPen(QtGui.QColor(C_DIM))
		p.setFont(QtGui.QFont("Courier New", 8))
		p.drawText(QtCore.QRect(0, h - 24, w - 16, 20), QtCore.Qt.AlignmentFlag.AlignRight, "[F4] MUTE")

		# ═══════════════════════════════════════════════════════════════════════════════
		# Data Stream - Binary/hex numbers flowing around outer rings
		# ═══════════════════════════════════════════════════════════════════════
		if self.tick % 3 == 0:
			if random.random() < 0.3 * _animation_intensity:
				chars = "01" + format(random.randint(0, 255), '02x')
				self._data_stream_chars.append({
					'char': random.choice(chars),
					'angle': random.uniform(0, 360),
					'dist': fw * 0.55 + random.uniform(-10, 10),
					'speed': random.uniform(0.5, 1.5) * _animation_intensity,
					'alpha': 180
				})

		p.setFont(QtGui.QFont("Courier New", 7))
		for ds in self._data_stream_chars[:]:
			ds['angle'] = (ds['angle'] + ds['speed']) % 360
			ds['alpha'] = max(0, ds['alpha'] - 4)
			if ds['alpha'] <= 0:
				self._data_stream_chars.remove(ds)
				continue
			rad = math.radians(ds['angle'])
			dx = fcx + ds['dist'] * math.cos(rad)
			dy = fcy + ds['dist'] * math.sin(rad)
			p.setPen(QtGui.QColor(C_MID))
			p.setOpacity(ds['alpha'] / 255)
			p.drawText(int(dx), int(dy), ds['char'])
		p.setOpacity(1.0)

		# ═══════════════════════════════════════════════════════════════════════
		# Energy Pulse - Radial energy burst on state transitions
		# ═══════════════════════════════════════════════════════════════════════
		if self._energy_pulse > 0:
			self._energy_pulse -= 3 * _animation_intensity
			pulse_r = int(self._energy_pulse * 3)
			pulse_alpha = max(0, int(self._energy_pulse * 8))
			if pulse_r > 0:
				p.setPen(QtGui.QPen(self._ac(0, 255, 136, pulse_alpha), 2))
				p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
				p.drawEllipse(QtCore.QPoint(fcx, fcy), pulse_r, pulse_r)

		# ═══════════════════════════════════════════════════════════════════════
		# Screen Shake Effect
		# ═══════════════════════════════════════════════════════════════════════════════
		if self._screen_shake > 0:
			shake_x = random.randint(-self._screen_shake, self._screen_shake)
			shake_y = random.randint(-self._screen_shake, self._screen_shake)
			p.translate(shake_x, shake_y)
			self._screen_shake = max(0, self._screen_shake - 1)

		# ═══════════════════════════════════════════════════════════════════════
		# Click Ripples - Animated ripple on clicks
		# ═══════════════════════════════════════════════════════════════════════
		for rip in _click_ripples[:]:
			rx, ry, age = rip
			age += 2 * _animation_intensity
			radius = int(age * 2)
			alpha = max(0, 255 - int(age * 5))
			if alpha <= 0:
				_click_ripples.remove(rip)
				continue
			p.setPen(QtGui.QPen(self._ac(0, 212, 255, alpha), 2))
			p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
			p.drawEllipse(QtCore.QPoint(rx, ry), radius, radius)
			_click_ripples[_click_ripples.index(rip)] = (rx, ry, age)

		# ═══════════════════════════════════════════════════════════════════════
		# Corner HUD Elements - System stats
		# ═══════════════════════════════════════════════════════════════════════
		hud_font = QtGui.QFont("Courier New", 7)
		p.setFont(hud_font)
		hud_alpha = 120

		# Top-left: Theme + Intensity
		p.setPen(QtGui.QColor(C_MID))
		p.drawText(8, 58, f"THEME:{self._get_theme_name()}")
		p.drawText(8, 70, f"INTEN:{_animation_intensity:.1f}x")

		# Top-right: Uptime
		p.setPen(QtGui.QColor(C_MID))
		p.drawText(QtCore.QRect(w - 80, 50, 72, 16), QtCore.Qt.AlignmentFlag.AlignRight, self._get_uptime())
		p.drawText(QtCore.QRect(w - 80, 62, 72, 16), QtCore.Qt.AlignmentFlag.AlignRight, f"MSG:{self._messages_sent}")

		# Bottom-left: FPS indicator (simple)
		if not hasattr(self, '_last_frame_time'):
			self._last_frame_time = time.time()
		elapsed = time.time() - self._last_frame_time
		if elapsed > 0:
			fps = int(1 / elapsed)
			p.setPen(QtGui.QColor(C_DIM))
			p.drawText(8, h - 38, f"FPS:{fps}")
		self._last_frame_time = time.time()


	def write_log(self, text: str) -> None:
		self.log_requested.emit(text)

	def _enqueue_log(self, text: str) -> None:
		self.typing_queue.append(text)
		tl = text.lower()
		if tl.startswith("you:"):
			self._set_state_impl("PROCESSING")
		elif tl.startswith("omini:") or tl.startswith("ai:"):
			self._set_state_impl("SPEAKING")
		if not self.is_typing:
			self._start_typing()

	def _start_typing(self) -> None:
		if not self.typing_queue:
			self.is_typing = False
			if not self.speaking and not self.muted:
				self._set_state_impl("LISTENING")
			return

		self.is_typing = True
		self._typing_text = self.typing_queue.popleft()
		self._typing_idx = 0
		tl = self._typing_text.lower()
		if tl.startswith("you:"):
			self._typing_color = QtGui.QColor("#e8e8e8")
		elif tl.startswith("omini:") or tl.startswith("ai:"):
			self._typing_color = QtGui.QColor(C_PRI)
		elif tl.startswith("err:") or "error" in tl or "failed" in tl:
			self._typing_color = QtGui.QColor(C_RED)
		else:
			self._typing_color = QtGui.QColor(C_ACC2)
		self._type_char()

	def _type_char(self) -> None:
		if self._typing_idx < len(self._typing_text):
			cursor = self.log_text.textCursor()
			cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
			self.log_text.setTextCursor(cursor)
			self.log_text.setTextColor(self._typing_color)
			self.log_text.insertPlainText(self._typing_text[self._typing_idx])
			self.log_text.ensureCursorVisible()
			self._typing_idx += 1
			QtCore.QTimer.singleShot(8, self._type_char)
			return

		self.log_text.insertPlainText("\n")
		self.log_text.ensureCursorVisible()
		QtCore.QTimer.singleShot(25, self._start_typing)

	def start_speaking(self) -> None:
		self.set_state("SPEAKING")

	def stop_speaking(self) -> None:
		if not self.muted:
			self.set_state("LISTENING")

	def _api_keys_exist(self) -> bool:
		if not API_FILE.exists():
			return False
		try:
			data = json.loads(API_FILE.read_text(encoding="utf-8"))
			return bool(data.get("gemini_api_key")) and bool(data.get("os_system"))
		except Exception:
			return False

	def wait_for_api_key(self) -> None:
		while not self._api_key_ready:
			time.sleep(0.1)

	@staticmethod
	def _detect_os() -> str:
		s = platform.system().lower()
		if s == "darwin":
			return "mac"
		if s == "windows":
			return "windows"
		return "linux"

	def _show_setup_ui(self) -> None:
		detected = self._detect_os()
		dlg = QtWidgets.QDialog(self)
		dlg.setModal(True)
		dlg.setWindowTitle("Initialisation")
		dlg.setStyleSheet(
			"QDialog { background:#00080d; border:1px solid #00d4ff; }"
			"QLabel { font-family:'Courier New'; }"
			"QLineEdit {"
			"background:#000d12; color:#8ffcff; border:1px solid #003344;"
			"padding:6px; font-family:'Courier New'; font-size:10pt; }"
			"QPushButton {"
			"font-family:'Courier New'; font-size:10pt; font-weight:700;"
			"border:1px solid #003344; padding:7px 10px; background:#000d12; color:#003344; }"
		)

		layout = QtWidgets.QVBoxLayout(dlg)
		layout.setContentsMargins(22, 18, 22, 18)
		layout.setSpacing(10)

		t1 = QtWidgets.QLabel("INITIALISATION REQUIRED")
		t1.setStyleSheet(f"color:{C_PRI}; font-size:13pt; font-weight:700;")
		layout.addWidget(t1, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

		t2 = QtWidgets.QLabel("Configure OMINI ASSISTANT before first boot.")
		t2.setStyleSheet(f"color:{C_MID}; font-size:9pt;")
		layout.addWidget(t2, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

		cap = QtWidgets.QLabel("GEMINI API KEY")
		cap.setStyleSheet(f"color:{C_DIM}; font-size:9pt;")
		layout.addWidget(cap)

		gemini_entry = QtWidgets.QLineEdit()
		gemini_entry.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
		layout.addWidget(gemini_entry)

		sep = QtWidgets.QFrame()
		sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
		sep.setStyleSheet(f"background:{C_DIM}; min-height:1px; max-height:1px;")
		layout.addWidget(sep)

		os_label = QtWidgets.QLabel("SELECT OPERATING SYSTEM")
		os_label.setStyleSheet(f"color:{C_DIM}; font-size:9pt;")
		layout.addWidget(os_label, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

		detect_label = {"windows": "Windows", "mac": "macOS", "linux": "Linux"}.get(detected, detected)
		auto = QtWidgets.QLabel(f"AUTO-DETECTED: {detect_label}")
		auto.setStyleSheet(f"color:{C_ACC2}; font-size:8pt;")
		layout.addWidget(auto, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

		os_row = QtWidgets.QHBoxLayout()
		os_row.setSpacing(8)
		layout.addLayout(os_row)

		group = QtWidgets.QButtonGroup(dlg)
		group.setExclusive(True)
		os_buttons: dict[str, QtWidgets.QPushButton] = {}

		options = [("windows", "WINDOWS"), ("mac", "macOS"), ("linux", "LINUX")]
		for key, label in options:
			b = QtWidgets.QPushButton(label)
			b.setCheckable(True)
			group.addButton(b)
			os_row.addWidget(b)
			os_buttons[key] = b

		selected_os = {"key": detected}

		def apply_os_style(active_key: str) -> None:
			styles = {
				"windows": (C_PRI, "#001a22"),
				"mac": (C_ACC2, "#1a1500"),
				"linux": (C_GREEN, "#001a0d"),
			}
			for k, b in os_buttons.items():
				if k == active_key:
					fg, bg = styles[k]
					b.setStyleSheet(
						"QPushButton {"
						f"background:{fg};"
						f"color:{bg};"
						"font-family:'Courier New'; font-size:10pt; font-weight:700;"
						"border:1px solid #003344; padding:7px 10px;"
						"}"
					)
					b.setChecked(True)
				else:
					b.setStyleSheet(
						"QPushButton {"
						"background:#000d12;"
						f"color:{C_DIM};"
						"font-family:'Courier New'; font-size:10pt; font-weight:700;"
						"border:1px solid #003344; padding:7px 10px;"
						"}"
					)
					b.setChecked(False)

		for key, btn in os_buttons.items():
			btn.clicked.connect(lambda _=False, k=key: (selected_os.__setitem__("key", k), apply_os_style(k)))

		apply_os_style(detected)

		sep2 = QtWidgets.QFrame()
		sep2.setFrameShape(QtWidgets.QFrame.Shape.HLine)
		sep2.setStyleSheet(f"background:{C_DIM}; min-height:1px; max-height:1px;")
		layout.addWidget(sep2)

		save_btn = QtWidgets.QPushButton("INITIALISE SYSTEMS")
		save_btn.setStyleSheet(
			"QPushButton {"
			f"background:{C_BG}; color:{C_PRI}; border:1px solid {C_MID};"
			"font-family:'Courier New'; font-size:10pt; font-weight:700; padding:8px;"
			"}"
			"QPushButton:hover { background:#003344; }"
		)
		layout.addWidget(save_btn)

		def on_save() -> None:
			gemini = gemini_entry.text().strip()
			if not gemini:
				gemini_entry.setStyleSheet(
					"QLineEdit {"
					"background:#000d12; color:#8ffcff; border:1px solid #ff3333;"
					"padding:6px; font-family:'Courier New'; font-size:10pt; }"
				)
				return

			os_system = selected_os["key"]
			os.makedirs(CONFIG_DIR, exist_ok=True)
			with open(API_FILE, "w", encoding="utf-8") as f:
				json.dump({"gemini_api_key": gemini, "os_system": os_system}, f, indent=4)

			self._api_key_ready = True
			self.set_state("LISTENING")
			self.write_log(f"SYS: Systems initialised. OS -> {os_system.upper()}. OMINI online.")
			dlg.accept()

		save_btn.clicked.connect(on_save)

		dlg.resize(560, 360)
		dlg.exec()

	def closeEvent(self, event: QtGui.QCloseEvent) -> None:
		event.accept()
		os._exit(0)

	# ═══════════════════════════════════════════════════════════════════════
	# Mouse Tracking - Parallax effect on orb position
	# ═══════════════════════════════════════════════════════════════════════
	def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
		global _click_ripples, _hover_highlights
		pos = event.position().toPoint()
		self._mouse_pos = (pos.x(), pos.y())

		# Calculate orb offset for parallax (subtle movement)
		dx = (pos.x() - self.FCX) / self.W * 15 * _animation_intensity
		dy = (pos.y() - self.FCY) / self.H * 15 * _animation_intensity
		self._orb_offset = (-dx, -dy)

		# Check hover on orb area
		dist = ((pos.x() - self.FCX) ** 2 + (pos.y() - self.FCY) ** 2) ** 0.5
		if dist < self.FACE_SZ // 2:
			self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
		else:
			self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)

		super().mouseMoveEvent(event)

	# ═══════════════════════════════════════════════════════════════════════════════
	# Click Ripples - Animated ripple effect on clicks
	# ═══════════════════════════════════════════════════════════════════════
	def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
		global _click_ripples
		pos = event.position().toPoint()
		_click_ripples.append((pos.x(), pos.y(), 0.0))
		super().mousePressEvent(event)

	# ═══════════════════════════════════════════════════════════════════════════════
	# Corner HUD - System stats display
	# ═══════════════════════════════════════════════════════════════════════════════
	def _get_uptime(self) -> str:
		elapsed = int(time.time() - self._start_time)
		h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
		return f"{h:02d}:{m:02d}:{s:02d}"

	def _get_theme_name(self) -> str:
		return _current_theme.upper()

	# ═══════════════════════════════════════════════════════════════════════
	# Theme & Settings Controls
	# ═══════════════════════════════════════════════════════════════════════
	def set_theme(self, theme_name: str) -> None:
		global _current_theme
		if theme_name in THEMES:
			_current_theme = theme_name

	def get_theme(self) -> str:
		return _current_theme

	def set_animation_intensity(self, intensity: float) -> None:
		global _animation_intensity
		_animation_intensity = max(0.1, min(2.0, intensity))

	def get_animation_intensity(self) -> float:
		return _animation_intensity

	def set_sound_enabled(self, enabled: bool) -> None:
		global _sound_enabled
		_sound_enabled = enabled

	def is_sound_enabled(self) -> bool:
		return _sound_enabled

	def trigger_screen_shake(self) -> None:
		self._screen_shake = 10

	def toggle_fullscreen(self) -> None:
		if self.isFullScreen():
			self.showNormal()
		else:
			self.showFullScreen()

	def increment_message_count(self) -> None:
		self._messages_sent += 1

