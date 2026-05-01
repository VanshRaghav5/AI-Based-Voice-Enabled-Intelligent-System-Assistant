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

try:
    from security import get_auth_manager, authenticate_user, continue_as_guest
    _SECURITY_AVAILABLE = True
except ImportError:
    _SECURITY_AVAILABLE = False

try:
    from core.persona_manager import get_persona_manager, list_personas
    _PERSONA_AVAILABLE = True
except ImportError:
    _PERSONA_AVAILABLE = False
    def get_persona_manager(): return None
    def list_personas(): return []

try:
    from core.voice_manager import get_voice_manager, list_voices
    _VOICE_AVAILABLE = True
except ImportError:
    _VOICE_AVAILABLE = False
    def get_voice_manager(): return None
    def list_voices(): return []

try:
    from core.voice_manager import get_live_voice_manager, list_live_voices
    _LIVE_VOICE_AVAILABLE = True
except ImportError:
    _LIVE_VOICE_AVAILABLE = False
    def get_live_voice_manager(): return None
    def list_live_voices(): return []


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR   = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE   = CONFIG_DIR / "api_keys.json"

SYSTEM_NAME = "O.M.I.N.I"
MODEL_BADGE  = "V3.0"

# ═══════════════════════════════════════════════════════════════════════════════
# THEME DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
THEMES = {
    "amethyst": {
        "name":           "AMETHYST",
        "bg":             "#04020C",
        "panel":          "#0D0820",
        "primary":        "#A855F7",
        "secondary":      "#5A2E8A",
        "accent":         "#3852B4",
        "accent2":        "#831C91",
        "dim":            "#2D1A55",
        "dimmer":         "#150D30",
        "text":           "#C4A8FF",
        "gold":           "#E0A8FF",
        "red":            "#CE2626",
        "muted_col":      "#C44545",
        "green":          "#7C3AED",
        "indigo":         "#462C7D",
        "header_bg":      "#06031A",
        "grid_col":       "#1A0F38",
        "eye_iris":       "#A855F7",
        "eye_pupil":      "#1A0040",
        "eye_sclera":     "#0D0820",
        "eye_vein":       "#5A2E8A",
        "eye_glow":       "#831C91",
        "eye_outer":      "#3852B4",
        "orb_mode":       "eye",
        "ring_style":     "orbital",
        "font_title":     "Courier New",
        "font_body":      "Courier New",
        "particle_col":   (168, 85, 247),
        "speak_rgb":      (56, 82, 180),
        "think_rgb":      (131, 28, 145),
        "listen_rgb":     (168, 85, 247),
        "mute_rgb":       (196, 69, 69),
    },
    "hogwarts": {
        "name":           "HOGWARTS",
        "bg":             "#050209",
        "panel":          "#0A0514",
        "primary":        "#C9A227",
        "secondary":      "#7B2D8B",
        "accent":         "#1E6B3C",
        "accent2":        "#8B1A1A",
        "dim":            "#3D2A0A",
        "dimmer":         "#1A0F05",
        "text":           "#F5DEB3",
        "gold":           "#FFD700",
        "red":            "#8B1A1A",
        "muted_col":      "#8B4513",
        "green":          "#1E6B3C",
        "indigo":         "#4B0082",
        "header_bg":      "#030109",
        "grid_col":       "#1A1005",
        "eye_iris":       "#C9A227",
        "eye_pupil":      "#0A0005",
        "eye_sclera":     "#0D0820",
        "eye_vein":       "#7B2D8B",
        "eye_glow":       "#FFD700",
        "eye_outer":      "#1E6B3C",
        "orb_mode":       "eye",
        "ring_style":     "runes",
        "font_title":     "Palatino Linotype",
        "font_body":      "Palatino Linotype",
        "particle_col":   (201, 162, 39),
        "speak_rgb":      (30, 107, 60),
        "think_rgb":      (123, 45, 139),
        "listen_rgb":     (201, 162, 39),
        "mute_rgb":       (139, 26, 26),
    },
    "avengers": {
        "name":           "AVENGERS",
        "bg":             "#000507",
        "panel":          "#021018",
        "primary":        "#00D4FF",
        "secondary":      "#003D55",
        "accent":         "#FF4500",
        "accent2":        "#FFB800",
        "dim":            "#003344",
        "dimmer":         "#001020",
        "text":           "#B0E8FF",
        "gold":           "#FFB800",
        "red":            "#FF2200",
        "muted_col":      "#FF4500",
        "green":          "#00FF88",
        "indigo":         "#0044AA",
        "header_bg":      "#000D14",
        "grid_col":       "#001A28",
        "eye_iris":       "#00D4FF",
        "eye_pupil":      "#000507",
        "eye_sclera":     "#002030",
        "eye_vein":       "#003D55",
        "eye_glow":       "#00D4FF",
        "eye_outer":      "#FFB800",
        "orb_mode":       "reactor",
        "ring_style":     "reactor_rings",
        "font_title":     "Courier New",
        "font_body":      "Courier New",
        "particle_col":   (0, 212, 255),
        "speak_rgb":      (255, 184, 0),
        "think_rgb":      (0, 212, 255),
        "listen_rgb":     (0, 255, 136),
        "mute_rgb":       (255, 34, 0),
    },
}

_current_theme       = "amethyst"
_animation_intensity = 1.0
_sound_enabled       = False
_click_ripples: list[list] = []

RUNE_CHARS  = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ✦✧⋆∗☆★◈◉○●"
LATIN_RUNES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789◈◉●○▷▶◀◁"
HOGWARTS_RUNES = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ✦✧⋆∗⚡🔮"


def T() -> dict:
    return THEMES[_current_theme]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: smooth color interpolation
# ═══════════════════════════════════════════════════════════════════════════════
def lerp_color(c1: str, c2: str, t: float) -> QtGui.QColor:
    a = QtGui.QColor(c1)
    b = QtGui.QColor(c2)
    r = int(a.red()   + (b.red()   - a.red())   * t)
    g = int(a.green() + (b.green() - a.green()) * t)
    bl = int(a.blue()  + (b.blue()  - a.blue())  * t)
    return QtGui.QColor(r, g, bl)


def make_col(hex_str: str, alpha: int) -> QtGui.QColor:
    c = QtGui.QColor(hex_str)
    c.setAlpha(max(0, min(255, alpha)))
    return c


def make_rgb(r: int, g: int, b: int, a: int) -> QtGui.QColor:
    c = QtGui.QColor(r, g, b)
    c.setAlpha(max(0, min(255, a)))
    return c


def safe_set_alpha(col: QtGui.QColor, a: float | int) -> None:
    # Ensure alpha is an integer in 0..255 before setting on QColor
    try:
        ai = int(a)
    except Exception:
        ai = 0
    col.setAlpha(max(0, min(255, ai)))


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
class LoginScreen(QtWidgets.QWidget):
    login_success = QtCore.Signal(str, str)

    def __init__(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        super().__init__()
        self._particles: list[dict] = []
        self._tick = 0
        self._setup_ui()
        self._anim = QtCore.QTimer(self)
        self._anim.timeout.connect(self._tick_anim)
        self._anim.start(16)

    def _tick_anim(self) -> None:
        self._tick += 1
        if self._tick % 5 == 0:
            t = T()
            r, g, b = t["particle_col"]
            self._particles.append({
                'x': random.uniform(0, self.width()),
                'y': self.height() + 10,
                'vx': random.uniform(-0.4, 0.4),
                'vy': random.uniform(-1.2, -0.3),
                'alpha': 160,
                'size': random.uniform(1.5, 4.5),
                'r': r, 'g': g, 'b': b,
                'pulse': random.uniform(0, math.pi * 2),
            })
        for pt in self._particles[:]:
            pt['x']     += pt['vx']
            pt['y']     += pt['vy']
            pt['alpha'] -= 1.8
            pt['pulse'] += 0.08
            if pt['alpha'] <= 0:
                self._particles.remove(pt)
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        t = T()
        p.fillRect(self.rect(), QtGui.QColor(t["bg"]))
        cg = QtGui.QRadialGradient(self.width() / 2, self.height() / 2, self.height() * 0.7)
        cg.setColorAt(0.0, make_col(t["primary"], 12))
        cg.setColorAt(1.0, QtGui.QColor(t["bg"]))
        p.fillRect(self.rect(), cg)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        for pt in self._particles:
            pulse_a = int(pt['alpha'] * (0.7 + 0.3 * math.sin(pt['pulse'])))
            col = make_rgb(pt['r'], pt['g'], pt['b'], max(0, pulse_a))
            p.setBrush(col)
            p.drawEllipse(QtCore.QPointF(pt['x'], pt['y']), pt['size'], pt['size'])

    def _setup_ui(self) -> None:
        self.setFixedSize(560, 700)
        self.setWindowTitle("OMINI — Secure Access")
        t = T()
        self.setStyleSheet(f"background: {t['bg']};")

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)

        card = QtWidgets.QWidget()
        card.setObjectName("authCard")
        card.setStyleSheet(f"""
            QWidget#authCard {{
                background: rgba(13,8,32,0.94);
                border: 1px solid {t['secondary']};
                border-radius: 24px;
            }}
        """)
        cl = QtWidgets.QVBoxLayout(card)
        cl.setContentsMargins(38, 32, 38, 32)
        cl.setSpacing(16)

        logo_row = QtWidgets.QHBoxLayout()
        logo_row.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        gem = QtWidgets.QLabel("◈")
        gem.setStyleSheet(f"color:{t['primary']}; font-size:34px; background:transparent;")
        title_lbl = QtWidgets.QLabel("O  M  I  N  I")
        title_lbl.setStyleSheet(f"""
            color: {t['primary']};
            font-family: '{t['font_title']}', monospace;
            font-size: 26px; font-weight: 700; letter-spacing: 10px;
            background: transparent;
        """)
        logo_row.addWidget(gem)
        logo_row.addSpacing(10)
        logo_row.addWidget(title_lbl)

        badge = QtWidgets.QLabel("◈  SECURE NEURAL ACCESS  ·  v3.0  ◈")
        badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"color:{t['dim']}; font-family:'Courier New',monospace; "
            f"font-size:8px; letter-spacing:4px; background:transparent;"
        )

        sep = self._make_sep()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {t['dim']}; border-radius: 14px;
                background: rgba(5,2,20,0.6);
            }}
            QTabBar::tab {{
                background: transparent; color: {t['dim']};
                padding: 10px 28px;
                border: 1px solid {t['dim']}; border-bottom: none;
                border-top-left-radius: 10px; border-top-right-radius: 10px;
                font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 3px;
            }}
            QTabBar::tab:selected {{
                background: rgba(13,8,32,0.85); color: {t['primary']};
                border-color: {t['secondary']};
            }}
            QTabBar::tab:hover:!selected {{ color: {t['text']}; }}
        """)

        field_ss = f"""
            QLineEdit {{
                background: {t['dimmer']}; color: {t['text']};
                border: 1px solid {t['dim']}; border-radius: 10px;
                padding: 12px 16px;
                font-family: '{t['font_body']}', monospace; font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {t['primary']}; background: {t['panel']};
            }}
        """

        self.si_user = self._field("Username",  field_ss)
        self.si_pass = self._field("Password",  field_ss, pw=True)
        self.si_btn  = self._primary_btn("◈  AUTHENTICATE")
        self.si_btn.clicked.connect(self._do_login)
        self.si_pass.returnPressed.connect(self._do_login)
        self.tabs.addTab(
            self._form_page("Welcome Back", [self.si_user, self.si_pass], self.si_btn, t),
            "  SIGN IN  "
        )

        self.su_user    = self._field("Choose username", field_ss)
        self.su_pass    = self._field("Create password", field_ss, pw=True)
        self.su_confirm = self._field("Confirm password", field_ss, pw=True)
        self.su_btn     = self._primary_btn("◉  FORGE IDENTITY")
        self.su_btn.clicked.connect(self._do_signup)
        self.tabs.addTab(
            self._form_page("New Identity", [self.su_user, self.su_pass, self.su_confirm], self.su_btn, t),
            "  REGISTER  "
        )

        self.msg_lbl = QtWidgets.QLabel("")
        self.msg_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet(
            f"color:{t['red']}; font-size:12px; background:transparent;"
        )

        guest_btn = QtWidgets.QPushButton("▷  Enter as Ghost")
        guest_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        guest_btn.setMinimumHeight(44)
        guest_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text']};
                border: 1px solid {t['dim']}; border-radius: 10px; padding: 11px;
                font-family: 'Courier New', monospace; font-size: 11px; letter-spacing: 2px;
            }}
            QPushButton:hover {{
                border: 1px solid {t['secondary']}; color: {t['primary']};
                background: rgba(13,8,32,0.5);
            }}
        """)
        guest_btn.clicked.connect(self._login_guest)

        ver = QtWidgets.QLabel("Neural Authentication  ·  Encrypted Vault  ·  Quantum Secured")
        ver.setStyleSheet(
            f"color:{t['dim']}; font-size:8px; letter-spacing:2px; background:transparent;"
        )
        ver.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        cl.addLayout(logo_row)
        cl.addWidget(badge)
        cl.addWidget(sep)
        cl.addWidget(self.tabs)
        cl.addWidget(self.msg_lbl)
        cl.addWidget(guest_btn)
        cl.addWidget(ver)
        root.addWidget(card)

    def _make_sep(self) -> QtWidgets.QFrame:
        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{T()['dim']}; border:none;")
        return sep

    def _field(self, ph: str, ss: str, pw: bool = False) -> QtWidgets.QLineEdit:
        w = QtWidgets.QLineEdit()
        w.setPlaceholderText(ph)
        w.setMinimumHeight(46)
        if pw:
            w.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        w.setStyleSheet(ss)
        return w

    def _primary_btn(self, text: str) -> QtWidgets.QPushButton:
        t = T()
        b = QtWidgets.QPushButton(text)
        b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        b.setMinimumHeight(48)
        b.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {t['indigo']}, stop:0.45 {t['accent2']}, stop:1 {t['primary']});
                color: #F8F0FF; border: none; border-radius: 10px; padding: 13px;
                font-family: '{t['font_body']}', monospace;
                font-size: 12px; font-weight: 700; letter-spacing: 3px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {t['secondary']}, stop:1 {t['primary']});
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        return b

    def _form_page(self, heading: str, fields: list, btn: QtWidgets.QPushButton, t: dict) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        page.setStyleSheet("background: transparent;")
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        h = QtWidgets.QLabel(heading)
        h.setStyleSheet(
            f"color:{t['gold']}; font-family:'{t['font_body']}',monospace; "
            f"font-size:15px; font-weight:600; background:transparent;"
        )
        layout.addWidget(h)
        for f in fields:
            layout.addWidget(f)
        layout.addSpacing(4)
        layout.addWidget(btn)
        layout.addStretch(1)
        return page

    def _set_message(self, text: str, success: bool = False) -> None:
        t = T()
        col = "#00FF88" if success else t["red"]
        self.msg_lbl.setText(text)
        self.msg_lbl.setStyleSheet(f"color:{col}; font-size:12px; background:transparent;")

    def _do_login(self) -> None:
        u, pw = self.si_user.text().strip(), self.si_pass.text()
        if not u or not pw:
            self._set_message("Credentials required.")
            return
        if _SECURITY_AVAILABLE:
            ok, msg = authenticate_user(u, pw)
            self._set_message(msg, success=ok)
            if ok:
                self.login_success.emit(u, "signin")
        else:
            self._set_message("Security module offline.")

    def _do_signup(self) -> None:
        u, pw, c = self.su_user.text().strip(), self.su_pass.text(), self.su_confirm.text()
        if not u or not pw:
            self._set_message("All fields required.")
            return
        if pw != c:
            self._set_message("Passwords do not match.")
            return
        if _SECURITY_AVAILABLE:
            am = get_auth_manager()
            if not am.create_user(u, pw):
                self._set_message("Identity already exists.")
                return
            ok, msg = authenticate_user(u, pw)
            if ok:
                self._set_message("Identity forged. Signing in…", success=True)
                self.login_success.emit(u, "signup")
            else:
                self._set_message(msg)
        else:
            self._set_message("Security module offline.")

    def _login_guest(self) -> None:
        if _SECURITY_AVAILABLE:
            ok, msg = continue_as_guest()
            self._set_message(msg, success=ok)
            if ok:
                self.login_success.emit("ghost", "guest")
        else:
            self._set_message("Security module offline.")

    def run(self) -> int:
        self.show()
        app = QtWidgets.QApplication.instance()
        return app.exec() if app else 0


# ═══════════════════════════════════════════════════════════════════════════════
# CENTRAL ORB WIDGET — Fully Interactive Eye | Arc Reactor | Magical Orb
# ═══════════════════════════════════════════════════════════════════════════════
class CentralOrbWidget(QtWidgets.QWidget):
    clicked       = QtCore.Signal()
    hover_changed = QtCore.Signal(bool)
    right_clicked = QtCore.Signal()

    def __init__(self, size: int, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setMouseTracking(True)
        self._size = size
        self._cx   = size // 2
        self._cy   = size // 2
        self._r    = size // 2 - 10

        # Core state
        self._tick          = 0
        self._hovered       = False
        self._pressed       = False
        self._scale         = 1.0
        self._target_scale  = 1.0
        self._halo_a        = 60.0
        self._target_halo   = 60.0
        self._speaking      = False
        self._muted         = False
        self._state         = "LISTENING"
        self._hover_glow    = 0.0
        self._energy_pulse  = 0.0
        self._click_flash   = 0.0   # white flash on click

        # Eye animation — highly detailed
        self._eye_open      = 1.0
        self._target_eye    = 1.0
        self._blink_cd      = random.randint(150, 320)
        self._double_blink  = False  # occasional double blink
        self._pupil_x       = 0.0
        self._pupil_y       = 0.0
        self._target_px     = 0.0
        self._target_py     = 0.0
        self._pupil_dilate  = 1.0   # pupil dilation 0.6..1.4
        self._iris_spin     = 0.0
        self._iris_spin2    = 0.0
        self._rune_spin     = 0.0
        self._rune_spin2    = 180.0
        self._cornea_phase  = 0.0
        self._vein_phase    = 0.0
        self._lid_droop     = 0.0
        self._tear_phase    = 0.0
        self._sclera_pulse  = 0.0   # sclera blood-shot pulsing
        self._iris_fractal  = 0.0   # iris fractal ring rotation
        self._eye_tilt      = 0.0   # subtle eye tilt for life
        self._target_tilt   = 0.0
        self._gaze_history: deque = deque(maxlen=8)  # smooth gaze trail
        # Iris detail layers
        self._iris_layers = [random.uniform(0, 360) for _ in range(6)]
        self._iris_layer_speeds = [random.uniform(0.1, 0.5) * (1 if i%2==0 else -1) for i in range(6)]

        # Hogwarts orb specific
        self._magic_orbs: list[dict] = []   # orbiting magical particles
        self._spell_cast = 0.0              # spell casting ring expansion
        self._crystal_spin = 0.0            # crystal facets rotation
        self._rune_positions = [
            (random.uniform(0, 360), random.choice(list(RUNE_CHARS)))
            for _ in range(32)
        ]
        self._rune_positions2 = [
            (random.uniform(0, 360), random.choice(list(HOGWARTS_RUNES)))
            for _ in range(20)
        ]

        # Reactor animation — Tony Stark grade
        self._reactor_spin  = [0.0, 30.0, 60.0, 90.0, 120.0]
        self._reactor_pulse = 0.0
        self._arc_phase     = 0.0
        self._bolt_pts: list[list] = []
        self._bolt_timer    = 0
        self._stark_breathe = 0.0
        self._reactor_charge = 0.0  # 0..1 charge indicator
        self._plasma_rings: list[float] = []  # plasma expansion rings
        self._core_flicker  = 1.0   # core brightness flicker
        self._hex_segments: list[dict] = []  # animated hex segments

        # Shared rings & particles
        self._rings_spin    = [0.0, 120.0, 240.0]
        self._scan_angle    = 0.0
        self._scan2_angle   = 180.0
        self._scan_fade     = [1.0, 0.6]  # scanner sweep opacity
        self._pulse_rings: list[float] = []
        self._particles:   list[dict]  = []
        self._trail_pts: deque = deque(maxlen=20)  # mouse trail around orb
        self._orb_aura      = 0.0
        self._interaction_glow = 0.0  # extra glow on interaction

        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        # Tooltip-style state label
        self._state_label_alpha = 0.0
        self._show_state_label  = False

    # ── Public interface ─────────────────────────────────────────────────────
    def set_state(self, state: str, speaking: bool = False, muted: bool = False) -> None:
        self._state    = state
        self._speaking = speaking
        self._muted    = muted
        self._show_state_label = True
        QtCore.QTimer.singleShot(2000, lambda: setattr(self, '_show_state_label', False))
        if speaking:
            self._target_scale = 1.10
            self._target_halo  = 200.0
            self._energy_pulse = 28.0
            self._pupil_dilate = 1.3  # dilated when speaking
        elif muted:
            self._target_scale = 0.98
            self._target_halo  = 18.0
            self._target_eye   = 0.18
            self._pupil_dilate = 0.7
        elif state == "THINKING":
            self._target_scale = 1.04
            self._target_halo  = 100.0
            self._pupil_dilate = 0.85
        elif state == "PROCESSING":
            self._target_scale = 1.06
            self._target_halo  = 130.0
            self._pupil_dilate = 0.9
        else:
            self._target_scale = 1.0
            self._target_halo  = 68.0
            self._target_eye   = 1.0
            self._pupil_dilate = 1.0
        self.update()

    def look_at(self, dx: float, dy: float) -> None:
        max_off = self._r * 0.12
        self._target_px = max(-max_off, min(max_off, dx * max_off))
        self._target_py = max(-max_off, min(max_off, dy * max_off))
        self._target_tilt = dx * 6.0  # subtle tilt toward gaze direction
        # Store gaze for trail effect
        self._gaze_history.append((
            self._cx + self._target_px,
            self._cy + self._target_py
        ))

    # ── Animation tick ───────────────────────────────────────────────────────
    def tick(self) -> None:
        self._tick += 1
        t  = T()
        sp = 0.32 if self._speaking else 0.15

        self._scale  += (self._target_scale - self._scale)  * sp
        self._halo_a += (self._target_halo  - self._halo_a) * sp

        self._pupil_x += (self._target_px - self._pupil_x) * 0.09
        self._pupil_y += (self._target_py - self._pupil_y) * 0.09
        self._eye_tilt += (self._target_tilt - self._eye_tilt) * 0.06

        tgt_h = 1.0 if self._hovered else 0.0
        self._hover_glow += (tgt_h - self._hover_glow) * 0.12
        self._interaction_glow = max(0.0, self._interaction_glow - 0.02)

        # State label fade
        tgt_la = 0.9 if self._show_state_label else 0.0
        self._state_label_alpha += (tgt_la - self._state_label_alpha) * 0.08

        # Click flash decay
        self._click_flash = max(0.0, self._click_flash - 0.04)

        # Eye mode — fully articulated
        if t["orb_mode"] == "eye":
            self._blink_cd -= 1
            if self._blink_cd <= 0:
                if self._eye_open > 0.5 and not self._muted:
                    self._target_eye = 0.0
                    self._blink_cd   = random.randint(6, 14)
                    self._double_blink = random.random() < 0.25
                else:
                    self._target_eye = 1.0 if not self._muted else 0.22
                    if self._double_blink:
                        self._blink_cd   = random.randint(8, 18)
                        self._double_blink = False
                    else:
                        self._blink_cd   = random.randint(100, 280)
            self._eye_open   += (self._target_eye - self._eye_open) * 0.28
            self._cornea_phase = (self._cornea_phase + 0.03) % (math.pi * 2)
            self._vein_phase   = (self._vein_phase   + 0.012) % (math.pi * 2)
            self._tear_phase   = (self._tear_phase   + 0.018) % (math.pi * 2)
            self._sclera_pulse = (self._sclera_pulse + 0.025) % (math.pi * 2)
            self._iris_fractal = (self._iris_fractal + (0.3 if self._speaking else 0.1)) % 360
            self._lid_droop    += (self._muted * 0.35 - self._lid_droop) * 0.06

            spd = 0.55 if self._speaking else 0.22
            self._iris_spin  = (self._iris_spin  + spd)        % 360
            self._iris_spin2 = (self._iris_spin2 - spd * 1.4)  % 360
            self._rune_spin  = (self._rune_spin  + (0.5 if self._speaking else 0.18)) % 360
            self._rune_spin2 = (self._rune_spin2 - 0.14) % 360

            # Update iris fractal layers
            for i in range(len(self._iris_layers)):
                spd_f = abs(self._iris_layer_speeds[i]) * (1.8 if self._speaking else 1.0)
                if self._iris_layer_speeds[i] < 0:
                    spd_f = -spd_f
                self._iris_layers[i] = (self._iris_layers[i] + spd_f) % 360

            # Pupil dilation animation
            target_dil = self._pupil_dilate
            # Natural micro-fluctuation
            target_dil += 0.04 * math.sin(self._tick * 0.05)
            current_dil = getattr(self, '_current_pupil_dil', 1.0)
            self._current_pupil_dil = current_dil + (target_dil - current_dil) * 0.05
            setattr(self, '_current_pupil_dil', self._current_pupil_dil)

        # Hogwarts orb magic particles
        if t["ring_style"] == "runes":
            # Spawn orbiting magic particles
            if self._tick % 4 == 0 and random.random() < 0.4:
                ang = random.uniform(0, 2 * math.pi)
                orb_r = self._r * random.uniform(0.55, 0.95)
                self._magic_orbs.append({
                    'angle': ang,
                    'radius': orb_r,
                    'speed': random.uniform(0.008, 0.025) * (1.5 if self._speaking else 1.0),
                    'alpha': random.randint(100, 200),
                    'size': random.uniform(2, 5),
                    'color_phase': random.uniform(0, math.pi * 2),
                    'decay': random.uniform(1.5, 3.0),
                    'type': random.choice(['star', 'dot', 'spark']),
                })
            for mo in self._magic_orbs[:]:
                mo['angle'] = (mo['angle'] + mo['speed']) % (2 * math.pi)
                mo['alpha'] -= mo['decay']
                mo['color_phase'] += 0.04
                if mo['alpha'] <= 0:
                    self._magic_orbs.remove(mo)

            self._crystal_spin = (self._crystal_spin + (0.4 if self._speaking else 0.15)) % 360
            self._spell_cast = max(0.0, self._spell_cast - 1.5)

        # Reactor mode
        if t["orb_mode"] == "reactor":
            rs = 2.8 if self._speaking else 1.0
            for i in range(len(self._reactor_spin)):
                dir_ = 1 if i % 2 == 0 else -1
                self._reactor_spin[i] = (self._reactor_spin[i] + rs * (1 + i * 0.25) * dir_) % 360
            self._arc_phase     = (self._arc_phase     + 0.09) % (math.pi * 2)
            self._reactor_pulse = (self._reactor_pulse + 0.06) % (math.pi * 2)
            self._stark_breathe = (self._stark_breathe + 0.04) % (math.pi * 2)
            self._reactor_charge = min(1.0, self._reactor_charge + (0.015 if self._speaking else 0.005))
            self._core_flicker  = 0.88 + 0.12 * math.sin(self._tick * 0.23 + 0.5)

            # Plasma rings
            pspd2 = 3.5 if self._speaking else 1.5
            limit2 = self._r * 1.1
            self._plasma_rings = [r2 + pspd2 for r2 in self._plasma_rings if r2 + pspd2 < limit2]
            if len(self._plasma_rings) < 5 and random.random() < (0.12 if self._speaking else 0.04):
                self._plasma_rings.append(self._r * 0.25)

            # Lightning bolts
            self._bolt_timer -= 1
            if self._bolt_timer <= 0:
                self._bolt_timer = random.randint(4, 14) if self._speaking else random.randint(20, 60)
                self._generate_bolt(t)
            for bolt in self._bolt_pts[:]:
                bolt[2] -= 18
                if bolt[2] <= 0:
                    self._bolt_pts.remove(bolt)

        # Shared ring spins
        spd2 = 1.6 if self._speaking else 0.6
        self._rings_spin[0] = (self._rings_spin[0] + spd2)        % 360
        self._rings_spin[1] = (self._rings_spin[1] - spd2 * 0.65) % 360
        self._rings_spin[2] = (self._rings_spin[2] + spd2 * 1.7)  % 360
        self._scan_angle    = (self._scan_angle  + (3.4 if self._speaking else 1.5)) % 360
        self._scan2_angle   = (self._scan2_angle - (2.1 if self._speaking else 0.8)) % 360
        self._orb_aura      = (self._orb_aura    + 0.04) % (math.pi * 2)

        # Pulse rings
        pspd  = 4.5 if self._speaking else 1.9
        limit = self._r * 1.18
        new_p = [r + pspd for r in self._pulse_rings if r + pspd < limit]
        if len(new_p) < 4 and random.random() < (0.09 if self._speaking else 0.025):
            new_p.append(0.0)
        self._pulse_rings = new_p

        # Particles
        if self._tick % 3 == 0 and _animation_intensity > 0.3:
            pr, pg, pb = t["particle_col"]
            ang = random.uniform(0, 2 * math.pi)
            r2  = self._r * (0.95 if t["orb_mode"] == "reactor" else 0.88)
            mult = (1.4 if self._speaking else 0.7)
            self._particles.append({
                'x': self._cx + r2 * math.cos(ang),
                'y': self._cy + r2 * math.sin(ang),
                'vx': random.uniform(-0.8, 0.8) * mult,
                'vy': random.uniform(-1.6, -0.2) * mult,
                'alpha': 210,
                'size': random.uniform(1.5, 5.0) * mult,
                'r': pr, 'g': pg, 'b': pb,
                'trail_len': random.randint(2, 6),
                'trail': [],
            })
        for pt in self._particles[:]:
            if 'trail' in pt:
                pt['trail'].append((pt['x'], pt['y']))
                if len(pt['trail']) > pt.get('trail_len', 3):
                    pt['trail'].pop(0)
            pt['x']     += pt['vx']
            pt['y']     += pt['vy']
            pt['alpha']  = max(0, pt['alpha'] - 6)
            if pt['alpha'] <= 0:
                self._particles.remove(pt)

        if self._energy_pulse > 0:
            self._energy_pulse -= 2.2
        self.update()

    def _generate_bolt(self, t: dict) -> None:
        cx, cy = self._cx, self._cy
        ang   = random.uniform(0, 2 * math.pi)
        r_in  = self._r * 0.30
        r_out = self._r * 0.78
        pts   = []
        steps = 11
        for i in range(steps + 1):
            fr  = i / steps
            cr  = r_in + (r_out - r_in) * fr
            jit = random.uniform(-12, 12) * fr * (1 - fr) * 4
            a2  = ang + jit * 0.06
            pts.append((cx + cr * math.cos(a2) + jit * 0.5, cy + cr * math.sin(a2) + jit * 0.5))
        r_, g_, b_ = t["particle_col"]
        self._bolt_pts.append([pts, random.uniform(80, 180), 255, r_, g_, b_])

    # ── Color helpers ─────────────────────────────────────────────────────────
    @staticmethod
    def _c(r: int, g: int, b: int, a: int) -> QtGui.QColor:
        col = QtGui.QColor(r, g, b)
        col.setAlpha(max(0, min(255, int(a))))
        return col

    def _get_state_rgb(self, t: dict) -> tuple:
        if self._muted:    return t["mute_rgb"]
        if self._speaking: return t["speak_rgb"]
        if self._state == "THINKING":   return t["think_rgb"]
        if self._state == "PROCESSING": return t["speak_rgb"]
        return t["listen_rgb"]

    # ── Master paint ─────────────────────────────────────────────────────────
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        p.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
        p.fillRect(self.rect(), QtCore.Qt.GlobalColor.transparent)
        t = T()

        # Click flash overlay
        if self._click_flash > 0:
            flash_a = int(self._click_flash * 60)
            p.fillRect(self.rect(), QtGui.QColor(255, 255, 255, flash_a))

        if t["orb_mode"] == "eye":
            self._paint_eye(p, t)
        elif t["orb_mode"] == "reactor":
            self._paint_reactor(p, t)
        else:
            self._paint_orb(p, t)

        # State label overlay
        if self._state_label_alpha > 0.05:
            self._paint_state_label(p, t)

    def _paint_state_label(self, p: QtGui.QPainter, t: dict) -> None:
        lbl = self._state
        if self._muted: lbl = "MUTED"
        p.setFont(QtGui.QFont("Courier New", 8, QtGui.QFont.Weight.Bold))
        fm   = p.fontMetrics()
        tw   = fm.horizontalAdvance(lbl) + 16
        th   = 18
        tx   = self._cx - tw // 2
        ty   = self._cy + self._r + 18
        a    = int(self._state_label_alpha * 200)
        bg   = QtGui.QColor(t["panel"])
        safe_set_alpha(bg, self._state_label_alpha * 180)
        brd  = QtGui.QColor(t["primary"])
        safe_set_alpha(brd, a)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(tx, ty, tw, th, 4, 4)
        p.setPen(brd)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(tx, ty, tw, th, 4, 4)
        txt_col = QtGui.QColor(t["primary"])
        safe_set_alpha(txt_col, a)
        p.setPen(txt_col)
        p.drawText(QtCore.QRect(tx, ty, tw, th), QtCore.Qt.AlignmentFlag.AlignCenter, lbl)

    # ═════════════════════════════════════════════════════════════════════════
    # EYE — The All-Seeing Arcane Eye
    # ═════════════════════════════════════════════════════════════════════════
    def _paint_eye(self, p: QtGui.QPainter, t: dict) -> None:
        cx, cy, r = self._cx, self._cy, self._r
        rgb   = self._get_state_rgb(t)
        sc    = self._scale
        eo    = self._eye_open

        # ── 1. Deep space / void background behind eye ─────────────────────
        void_grad = QtGui.QRadialGradient(float(cx), float(cy), float(r * 1.15))
        void_grad.setColorAt(0.0,  make_rgb(*rgb, int(8 + 6 * math.sin(self._tick * 0.02))))
        void_grad.setColorAt(0.45, make_rgb(*rgb, int(4 + 3 * math.sin(self._tick * 0.02))))
        void_grad.setColorAt(1.0,  QtGui.QColor(0, 0, 0, 0))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QBrush(void_grad))
        p.drawEllipse(QtCore.QPoint(cx, cy), int(r * 1.15), int(r * 1.15))

        # ── 2. Outer atmospheric halo rings ────────────────────────────────
        halo_layers = 9
        for i in range(halo_layers, 0, -1):
            fr    = i / halo_layers
            hr2   = int(r * (1.06 + fr * 0.32))
            ha    = max(0, int(self._halo_a * 0.13 * fr * (1 + self._hover_glow * 0.9)))
            col   = self._c(*rgb, ha)
            pen_w = 1.5 + fr * 0.5
            p.setPen(QtGui.QPen(col, pen_w))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QtCore.QPoint(cx, cy), hr2, hr2)

        # ── 3. Outer rune / character ring ─────────────────────────────────
        rune_r = int(r * 1.04)
        sr     = t["ring_style"]
        if sr == "runes":
            # Hogwarts — two counter-rotating rune rings
            p.setFont(QtGui.QFont(t["font_body"], 8, QtGui.QFont.Weight.Bold))
            for (base_a, char) in self._rune_positions:
                ang = math.radians((base_a + self._rune_spin) % 360)
                rx  = cx + rune_r * math.cos(ang)
                ry  = cy + rune_r * math.sin(ang)
                pulse_a = int(55 + 90 * abs(math.sin(ang * 2 + self._vein_phase)))
                gold_c  = QtGui.QColor(t["gold"])
                safe_set_alpha(gold_c, min(190, pulse_a))
                p.setPen(gold_c)
                p.drawText(QtCore.QPointF(rx - 5, ry + 4), char)
            # Second ring
            rune_r2 = int(r * 0.96)
            p.setFont(QtGui.QFont(t["font_body"], 5))
            for (base_a2, char2) in self._rune_positions2:
                ang2 = math.radians((base_a2 + self._rune_spin2) % 360)
                rx2  = cx + rune_r2 * math.cos(ang2)
                ry2  = cy + rune_r2 * math.sin(ang2)
                sec_c = QtGui.QColor(t["secondary"])
                safe_set_alpha(sec_c, 50)
                p.setPen(sec_c)
                p.drawText(QtCore.QPointF(rx2 - 3, ry2 + 3), char2)
        else:
            # Amethyst — orbital tick ring
            tick_r = rune_r
            for deg in range(0, 360, 6):
                rad = math.radians(deg + self._rings_spin[0])
                is_major = (deg % 45 == 0)
                is_mid   = (deg % 15 == 0)
                inn = tick_r - (14 if is_major else (8 if is_mid else 4))
                lw  = 2.5 if is_major else (1.5 if is_mid else 0.8)
                a_t = 130 if is_major else (80 if is_mid else 40)
                p.setPen(QtGui.QPen(self._c(*rgb, a_t), lw))
                p.drawLine(
                    QtCore.QPointF(cx + tick_r * math.cos(rad), cy + tick_r * math.sin(rad)),
                    QtCore.QPointF(cx + inn   * math.cos(rad), cy + inn   * math.sin(rad)),
                )
            # Degree labels at cardinal points
            p.setFont(QtGui.QFont("Courier New", 5))
            for deg in [0, 90, 180, 270]:
                rad = math.radians(deg + self._rings_spin[0])
                lx  = cx + (tick_r + 8) * math.cos(rad)
                ly  = cy + (tick_r + 8) * math.sin(rad)
                c2  = self._c(*rgb, 60)
                p.setPen(c2)
                p.drawText(QtCore.QPointF(lx - 6, ly + 4), f"{deg}°")

        # ── 4. Multi-layer spinning arc rings ─────────────────────────────
        ring_specs = [
            (0.93, 2.5, 85, 35, 1.0),
            (0.84, 2.0, 60, 48, 0.85),
            (0.75, 1.5, 42, 55, 0.7),
            (0.66, 1.0, 28, 62, 0.55),
        ]
        for idx, (rfrac, lw, arc_span, arc_gap, opacity) in enumerate(ring_specs):
            rr2  = int(r * rfrac)
            a_v  = max(0, min(255, int(self._halo_a * opacity * (0.85 - idx * 0.12))))
            col  = self._c(*rgb, a_v)
            p.setPen(QtGui.QPen(col, lw))
            base = self._rings_spin[idx % 3]
            if idx % 2 == 1:
                base = -base
            rect = QtCore.QRectF(cx - rr2, cy - rr2, rr2 * 2, rr2 * 2)
            seg  = arc_span + arc_gap
            for s in range(360 // seg + 1):
                start = (base + s * seg) % 360
                p.drawArc(rect, int(-start * 16), int(-arc_span * 16))

        # ── 5. Scanner sweeps (dual) ───────────────────────────────────────
        sr_r = int(r * 0.97)
        sa   = min(255, int(self._halo_a * 1.8))
        ext1 = 110 if self._speaking else 65
        # Primary scanner with gradient
        for sw in range(ext1, 0, -8):
            sa_sw = int(sa * (sw / ext1) * 0.7)
            p.setPen(QtGui.QPen(self._c(*rgb, sa_sw), 2))
            p.drawArc(
                QtCore.QRectF(cx - sr_r, cy - sr_r, sr_r * 2, sr_r * 2),
                int(-self._scan_angle * 16), int(-sw * 16)
            )
        # Secondary scanner
        p.setPen(QtGui.QPen(self._c(*rgb, sa // 3), 1.5))
        p.drawArc(
            QtCore.QRectF(cx - sr_r, cy - sr_r, sr_r * 2, sr_r * 2),
            int(-self._scan2_angle * 16), int(-40 * 16)
        )

        # ── 6. Sclera ─────────────────────────────────────────────────────
        eye_r = int(r * 0.62 * sc)
        p.save()
        p.translate(cx, cy)
        p.rotate(self._eye_tilt)
        p.scale(1.0, eo * (1.0 - self._lid_droop * 0.4))

        scl_grad = QtGui.QRadialGradient(eye_r * -0.08, eye_r * -0.12, eye_r)
        scl_base = QtGui.QColor(t["eye_sclera"])
        scl_grad.setColorAt(0.0,  scl_base.lighter(145))
        scl_grad.setColorAt(0.45, scl_base)
        scl_grad.setColorAt(0.78, QtGui.QColor(t["eye_vein"]).darker(80))
        scl_grad.setColorAt(1.0,  QtGui.QColor(t["eye_outer"]).darker(55))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QBrush(scl_grad))
        p.drawEllipse(QtCore.QPoint(0, 0), eye_r, eye_r)
        p.restore()

        if eo > 0.04:
            # ── 7. Sclera vein network ─────────────────────────────────────
            p.save()
            p.translate(cx, cy)
            p.rotate(self._eye_tilt)
            p.scale(1.0, eo * (1.0 - self._lid_droop * 0.4))
            vein_col = QtGui.QColor(t["eye_vein"])
            for i in range(16):
                ang_v   = math.radians(i * 22.5 + self._vein_phase * 8)
                r_vein  = eye_r * random.uniform(0.52, 0.74)
                pulse_v = 0.45 + 0.55 * math.sin(self._sclera_pulse + i * 0.7)
                # Extra red tint when speaking (bloodshot)
                va = int((28 if self._speaking else 18) * pulse_v * _animation_intensity)
                safe_set_alpha(vein_col, va)
                p.setPen(QtGui.QPen(vein_col, 0.8))
                mid_r  = r_vein * 0.55
                mid_a  = ang_v + random.uniform(-0.25, 0.25)
                x1, y1 = eye_r * 0.5 * math.cos(ang_v), eye_r * 0.5 * math.sin(ang_v)
                mx, my = mid_r * math.cos(mid_a), mid_r * math.sin(mid_a)
                path_v = QtGui.QPainterPath(QtCore.QPointF(x1, y1))
                path_v.quadTo(QtCore.QPointF(mx, my), QtCore.QPointF(0, 0))
                p.strokePath(path_v, p.pen())
            p.restore()

            # ── 8. IRIS — the centerpiece ─────────────────────────────────
            iris_r = int(eye_r * 0.72)
            p.save()
            p.translate(cx, cy)
            p.rotate(self._eye_tilt)
            p.scale(1.0, eo * (1.0 - self._lid_droop * 0.4))

            # Iris base — rich layered gradient
            iris_grad = QtGui.QRadialGradient(
                iris_r * 0.1 + self._pupil_x * 0.05,
                iris_r * 0.08 + self._pupil_y * 0.05,
                float(iris_r)
            )
            iris_col  = QtGui.QColor(t["eye_iris"])
            iris_grad.setColorAt(0.0,  QtGui.QColor(t["eye_pupil"]).lighter(130))
            iris_grad.setColorAt(0.18, iris_col.darker(160))
            iris_grad.setColorAt(0.38, iris_col.darker(110))
            iris_grad.setColorAt(0.58, iris_col)
            iris_grad.setColorAt(0.78, iris_col.lighter(120))
            iris_grad.setColorAt(0.92, QtGui.QColor(t["eye_vein"]).lighter(90))
            iris_grad.setColorAt(1.0,  QtGui.QColor(t["eye_vein"]))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(QtGui.QBrush(iris_grad))
            p.drawEllipse(QtCore.QPoint(0, 0), iris_r, iris_r)

            # Iris texture layers — multiple rotating petal rings
            for layer_idx, (layer_ang, layer_spd) in enumerate(
                zip(self._iris_layers, self._iris_layer_speeds)
            ):
                petal_cnt = [32, 24, 18, 14, 10, 8][layer_idx]
                r_in_frac = [0.40, 0.50, 0.58, 0.65, 0.70, 0.74][layer_idx]
                r_out_frac= [0.95, 0.88, 0.82, 0.76, 0.71, 0.67][layer_idx]
                opacity   = [70, 55, 45, 38, 30, 25][layer_idx]
                a_layer   = int(opacity * (1 + 0.3 * math.sin(self._cornea_phase + layer_idx)))
                p.setPen(QtGui.QPen(self._c(*rgb, a_layer), 0.8))
                for i in range(petal_cnt):
                    ang_p = math.radians(layer_ang + i * (360 / petal_cnt))
                    p.drawLine(
                        QtCore.QPointF(iris_r * r_in_frac  * math.cos(ang_p),
                                       iris_r * r_in_frac  * math.sin(ang_p)),
                        QtCore.QPointF(iris_r * r_out_frac * math.cos(ang_p),
                                       iris_r * r_out_frac * math.sin(ang_p)),
                    )

            # Iris concentric detail rings
            for rf in [0.25, 0.42, 0.58, 0.72, 0.86, 0.95]:
                a_r = int(55 + 38 * math.sin(self._cornea_phase * 1.3 + rf * 5.2))
                p.setPen(QtGui.QPen(self._c(*rgb, a_r), 0.8 + rf * 0.4))
                p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                p.drawEllipse(QtCore.QPoint(0, 0), int(iris_r * rf), int(iris_r * rf))

            # Iris fractal hexagon pattern (advanced detail)
            hex_r_i = int(iris_r * 0.52)
            hex_col = self._c(*rgb, 35)
            p.setPen(QtGui.QPen(hex_col, 0.7))
            p.save()
            p.rotate(self._iris_fractal)
            for i in range(6):
                ang_h = math.radians(i * 60)
                hx = hex_r_i * math.cos(ang_h)
                hy = hex_r_i * math.sin(ang_h)
                # Small hexagon at each point
                sub_r = hex_r_i * 0.28
                sub_pts = [
                    QtCore.QPointF(hx + sub_r * math.cos(math.radians(j * 60)),
                                   hy + sub_r * math.sin(math.radians(j * 60)))
                    for j in range(6)
                ]
                p.drawPolygon(sub_pts)
            p.restore()

            # Iris limbus (dark border)
            limbus_col = QtGui.QColor(t["eye_vein"])
            safe_set_alpha(limbus_col, 140)
            p.setPen(QtGui.QPen(limbus_col, 4))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QtCore.QPoint(0, 0), iris_r, iris_r)
            p.restore()

            # ── 9. Pupil — gaze-tracking with dilation ────────────────────
            cur_dil = getattr(self, '_current_pupil_dil', 1.0)
            pup_r = int(iris_r * 0.34 * cur_dil)
            px_   = int(self._pupil_x)
            py_   = int(self._pupil_y)

            p.save()
            p.translate(cx, cy)
            p.rotate(self._eye_tilt)
            p.scale(1.0, eo * (1.0 - self._lid_droop * 0.4))

            # Pupil — deep void with radial gradient
            pup_grad = QtGui.QRadialGradient(
                float(px_) * 0.25, float(py_) * 0.25, float(pup_r)
            )
            pup_grad.setColorAt(0.0,  QtGui.QColor(t["eye_pupil"]).lighter(160))
            pup_grad.setColorAt(0.3,  QtGui.QColor(t["eye_pupil"]).lighter(120))
            pup_grad.setColorAt(0.65, QtGui.QColor(t["eye_pupil"]))
            pup_grad.setColorAt(0.88, QtGui.QColor(t["eye_iris"]).darker(220))
            pup_grad.setColorAt(1.0,  QtGui.QColor(t["eye_vein"]).darker(160))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(QtGui.QBrush(pup_grad))
            p.drawEllipse(QtCore.QPointF(float(px_), float(py_)), float(pup_r), float(pup_r))

            # Pupil inner abyss shimmer
            if self._speaking or self._state == "THINKING":
                abyss_r = int(pup_r * 0.55)
                abyss_grad = QtGui.QRadialGradient(float(px_), float(py_), float(abyss_r))
                ar, ag, ab = rgb
                abyss_grad.setColorAt(0.0, self._c(ar, ag, ab, int(40 + 30 * math.sin(self._tick * 0.08))))
                abyss_grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
                p.setBrush(QtGui.QBrush(abyss_grad))
                p.drawEllipse(QtCore.QPointF(float(px_), float(py_)), float(abyss_r), float(abyss_r))

            # Specular highlights
            hl_r = max(2, pup_r // 3)
            hl_col = QtGui.QColor(t["eye_iris"]).lighter(220)
            safe_set_alpha(hl_col, min(255, int(145 + 65 * math.sin(self._cornea_phase))))
            p.setBrush(hl_col)
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawEllipse(
                QtCore.QPointF(float(px_) - pup_r * 0.3, float(py_) - pup_r * 0.34),
                float(hl_r), float(hl_r)
            )
            hl2_col = QtGui.QColor("#FFFFFF")
            safe_set_alpha(hl2_col, 70)
            p.setBrush(hl2_col)
            p.drawEllipse(
                QtCore.QPointF(float(px_) + pup_r * 0.2, float(py_) - pup_r * 0.25),
                float(max(1, hl_r // 2)), float(max(1, hl_r // 2))
            )
            # Tiny third highlight for depth
            hl3_col = QtGui.QColor("#FFFFFF")
            safe_set_alpha(hl3_col, 35)
            p.setBrush(hl3_col)
            p.drawEllipse(
                QtCore.QPointF(float(px_) - pup_r * 0.05, float(py_) + pup_r * 0.3),
                float(max(1, hl_r // 3)), float(max(1, hl_r // 3))
            )
            p.restore()

            # ── 10. Corneal shimmer ────────────────────────────────────────
            p.save()
            p.translate(cx, cy)
            p.rotate(self._eye_tilt)
            p.scale(1.0, eo)
            cornea_grad = QtGui.QRadialGradient(-eye_r * 0.28, -eye_r * 0.32, eye_r * 0.6)
            cs_a = int(22 + 20 * math.sin(self._cornea_phase))
            cornea_grad.setColorAt(0.0, QtGui.QColor(255, 255, 255, cs_a))
            cornea_grad.setColorAt(0.5, QtGui.QColor(255, 255, 255, cs_a // 3))
            cornea_grad.setColorAt(1.0, QtGui.QColor(255, 255, 255, 0))
            p.setBrush(QtGui.QBrush(cornea_grad))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawEllipse(QtCore.QPoint(0, 0), eye_r, eye_r)
            p.restore()

            # ── 11. Hogwarts magical tear/spell drops ─────────────────────
            if sr == "runes":
                for mo in self._magic_orbs:
                    mx_ = cx + mo['radius'] * math.cos(mo['angle'])
                    my_ = cy + mo['radius'] * math.sin(mo['angle'])
                    color_r = int(201 + 40 * math.sin(mo['color_phase']))
                    color_g = int(162 + 40 * math.cos(mo['color_phase']))
                    color_b = int(39  + 30 * math.sin(mo['color_phase'] * 0.7))
                    mc = self._c(min(255, color_r), min(255, color_g), min(255, color_b),
                                 int(mo['alpha']))
                    p.setPen(QtCore.Qt.PenStyle.NoPen)
                    p.setBrush(mc)
                    if mo['type'] == 'star':
                        sz = mo['size']
                        for si in range(4):
                            ang_s = math.radians(si * 45 + self._crystal_spin)
                            p.drawEllipse(
                                QtCore.QPointF(mx_ + sz * math.cos(ang_s), my_ + sz * math.sin(ang_s)),
                                1.0, 1.0
                            )
                        p.drawEllipse(QtCore.QPointF(mx_, my_), mo['size'] * 0.6, mo['size'] * 0.6)
                    else:
                        p.drawEllipse(QtCore.QPointF(mx_, my_), mo['size'], mo['size'])

                # Crystal facet glow when speaking
                if self._speaking:
                    for i in range(8):
                        ang_c = math.radians(self._crystal_spin + i * 45)
                        cr_   = eye_r * 0.74
                        cxf   = cx + cr_ * math.cos(ang_c)
                        cyf   = cy + cr_ * math.sin(ang_c)
                        gc    = self._c(255, 215, 0, int(40 + 40 * math.sin(self._cornea_phase + i)))
                        p.setBrush(gc)
                        p.drawEllipse(QtCore.QPointF(cxf, cyf), 3, 3)

        # ── 12. Eyelids ────────────────────────────────────────────────────
        if eo < 0.99 or self._lid_droop > 0.02:
            effective_close = max(0.0, 1.0 - eo + self._lid_droop * 0.5)
            lid_bg  = QtGui.QColor(t["bg"])
            eye_r_l = int(r * 0.62 * sc)
            lid_h   = int(eye_r_l * (1.1 + self._lid_droop * 0.25))
            lid_shift = int(lid_h * effective_close * 0.92)
            safe_set_alpha(lid_bg, 255 * min(1.0, effective_close * 1.5))
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(lid_bg)
            p.save()
            p.translate(cx, cy)
            p.rotate(self._eye_tilt)
            p.translate(-cx, -cy)
            # Top lid — slightly curved
            p.drawEllipse(QtCore.QRect(cx - eye_r_l, cy - lid_h * 2 + lid_shift, eye_r_l * 2, lid_h * 2))
            # Bottom lid
            p.drawEllipse(QtCore.QRect(cx - eye_r_l, cy + lid_h - lid_shift, eye_r_l * 2, lid_h * 2))
            p.restore()

            # Lash / lid edge highlight
            if effective_close > 0.05:
                eye_r_l2 = int(r * 0.62 * sc)
                lash_y_top = cy - int(eye_r_l2 * eo * 0.85)
                lash_y_bot = cy + int(eye_r_l2 * eo * 0.85)
                lash_col = QtGui.QColor(t["eye_vein"])
                safe_set_alpha(lash_col, 80 * effective_close)
                p.setPen(QtGui.QPen(lash_col, 2))
                p.drawLine(cx - eye_r_l2, lash_y_top, cx + eye_r_l2, lash_y_top)
                p.drawLine(cx - eye_r_l2, lash_y_bot, cx + eye_r_l2, lash_y_bot)

        # ── 13. Eye border glow ring ───────────────────────────────────────
        p.save()
        p.translate(cx, cy)
        p.rotate(self._eye_tilt)
        p.scale(1.0, eo * (1.0 - self._lid_droop * 0.4))
        eye_r3 = int(r * 0.62 * self._scale)
        border_a = min(255, int(self._halo_a * 2.4))
        # Outer glow
        p.setPen(QtGui.QPen(self._c(*rgb, border_a // 2), 6))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QtCore.QPoint(0, 0), eye_r3, eye_r3)
        # Sharp border
        p.setPen(QtGui.QPen(self._c(*rgb, border_a), 2.5))
        p.drawEllipse(QtCore.QPoint(0, 0), eye_r3, eye_r3)
        # Inner detail ring
        p.setPen(QtGui.QPen(self._c(*rgb, border_a // 4), 1))
        p.drawEllipse(QtCore.QPoint(0, 0), eye_r3 - 5, eye_r3 - 5)
        p.restore()

        # ── 14. Pulse rings, particles, energy ─────────────────────────────
        self._paint_pulse_rings(p, rgb)
        self._paint_shared_particles(p)
        self._paint_energy_pulse(p, rgb)

    # ═════════════════════════════════════════════════════════════════════════
    # ARC REACTOR — Tony Stark Grade
    # ═════════════════════════════════════════════════════════════════════════
    def _paint_reactor(self, p: QtGui.QPainter, t: dict) -> None:
        cx, cy, r = self._cx, self._cy, self._r
        rgb = self._get_state_rgb(t)
        sc  = self._scale

        # ── 1. Deep space electromagnetic field ────────────────────────────
        for i in range(10, 0, -1):
            fr    = i / 10
            hr2   = int(r * (1.04 + fr * 0.26))
            ha    = max(0, int(self._halo_a * 0.15 * fr * (1 + self._hover_glow * 0.8)))
            p.setPen(QtGui.QPen(self._c(*rgb, ha), 1.5))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QtCore.QPoint(cx, cy), hr2, hr2)

        # ── 2. Outer rotating segmented rings (5 layers) ───────────────────
        ring_defs = [
            (0.98, 6,   4, "primary",   140),
            (0.90, 10,  3, "accent2",   120),
            (0.82, 16,  2, "primary",   100),
            (0.74, 22,  1, "accent",    80),
            (0.66, 30,  1, "secondary", 60),
        ]
        for idx, (rfrac, seg_cnt, lw, col_key, base_alpha) in enumerate(ring_defs):
            ring_r2 = int(r * rfrac)
            col     = QtGui.QColor(t[col_key])
            av2     = min(255, int(base_alpha * (self._halo_a / 80) * self._core_flicker))
            safe_set_alpha(col, av2)
            p.setPen(QtGui.QPen(col, lw))
            base     = self._reactor_spin[idx % len(self._reactor_spin)]
            rect_r   = QtCore.QRectF(cx - ring_r2, cy - ring_r2, ring_r2 * 2, ring_r2 * 2)
            seg_span = max(4, (360 // seg_cnt) - 8)
            for s in range(seg_cnt):
                start = (base + s * (360 // seg_cnt)) % 360
                p.drawArc(rect_r, int(-start * 16), int(-seg_span * 16))
            # Connecting dots at segment ends
            if idx <= 2:
                dot_col = QtGui.QColor(t[col_key])
                safe_set_alpha(dot_col, av2 // 2)
                p.setPen(QtCore.Qt.PenStyle.NoPen)
                p.setBrush(dot_col)
                for s in range(seg_cnt):
                    ang_d = math.radians(base + s * (360 // seg_cnt))
                    dx_   = cx + ring_r2 * math.cos(ang_d)
                    dy_   = cy + ring_r2 * math.sin(ang_d)
                    p.drawEllipse(QtCore.QPointF(dx_, dy_), 2.0, 2.0)

        # ── 3. Star polygon (overlapping triangles) ───────────────────────
        tri_r = int(r * 0.67 * sc)
        p.save()
        p.translate(cx, cy)
        p.rotate(self._reactor_spin[0] * 0.45)
        for rot, alpha_frac in [(0, 1.0), (60, 0.7)]:
            tri_col = QtGui.QColor(t["primary"])
            safe_set_alpha(tri_col, min(255, int(self._halo_a * 1.4 * alpha_frac * self._core_flicker)))
            p.setPen(QtGui.QPen(tri_col, 2.5))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            pts_tri = [
                QtCore.QPointF(tri_r * math.cos(math.radians(90 + rot + i * 120)),
                               tri_r * math.sin(math.radians(90 + rot + i * 120)))
                for i in range(3)
            ]
            p.drawPolygon(pts_tri)
        p.restore()

        # ── 4. Hexagonal inner frame ──────────────────────────────────────
        hex_r = int(r * 0.55 * sc)
        p.save()
        p.translate(cx, cy)
        p.rotate(self._reactor_spin[1] * 0.28)
        for hsize, halpha, hrot in [(1.0, 1.8, 0), (0.75, 0.8, 15), (0.55, 0.5, 0)]:
            hr_sz = int(hex_r * hsize)
            hf_col = QtGui.QColor(t["accent2"])
            safe_set_alpha(hf_col, min(255, int(self._halo_a * halpha * self._core_flicker)))
            p.setPen(QtGui.QPen(hf_col, max(1, int(3 * hsize))))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.save()
            p.rotate(hrot)
            hex_pts = [
                QtCore.QPointF(hr_sz * math.cos(math.radians(i * 60)),
                               hr_sz * math.sin(math.radians(i * 60)))
                for i in range(6)
            ]
            p.drawPolygon(hex_pts)
            p.restore()
        p.restore()

        # ── 5. Spoke lines ─────────────────────────────────────────────────
        spoke_in  = int(r * 0.30 * sc)
        spoke_out = int(r * 0.53 * sc)
        p.save()
        p.translate(cx, cy)
        p.rotate(self._reactor_spin[2] * 0.2)
        for spoke_set, sp_cnt, sp_alpha in [(0, 10, 1.0), (18, 10, 0.4)]:
            sp_col = QtGui.QColor(t["primary"])
            safe_set_alpha(sp_col, min(255, int(self._halo_a * 0.9 * sp_alpha * self._core_flicker)))
            p.setPen(QtGui.QPen(sp_col, 2 if sp_alpha > 0.5 else 1))
            for i in range(sp_cnt):
                ang_s = math.radians(i * 36 + spoke_set)
                p.drawLine(
                    QtCore.QPointF(spoke_in  * math.cos(ang_s), spoke_in  * math.sin(ang_s)),
                    QtCore.QPointF(spoke_out * math.cos(ang_s), spoke_out * math.sin(ang_s)),
                )
        p.restore()

        # ── 6. Toroid ring with breath animation ──────────────────────────
        tor_r   = int(r * 0.35 * sc)
        breathe = 0.91 + 0.09 * math.sin(self._stark_breathe)
        tor_rb  = int(tor_r * breathe)

        # Toroid glow layers
        for i in range(8, 0, -1):
            fr     = i / 8
            tg_r   = int(tor_rb * (1 + fr * 0.18))
            ta     = max(0, int(self._halo_a * 0.2 * fr * self._core_flicker))
            p.setPen(QtGui.QPen(self._c(*rgb, ta), 2))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QtCore.QPoint(cx, cy), tg_r, tg_r)

        tor_col = QtGui.QColor(t["primary"])
        safe_set_alpha(tor_col, min(255, int(self._halo_a * 3.0 * self._core_flicker)))
        p.setPen(QtGui.QPen(tor_col, 5))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QtCore.QPoint(cx, cy), tor_rb, tor_rb)
        # Inner toroid
        tor_col2 = QtGui.QColor(t["accent2"])
        safe_set_alpha(tor_col2, min(255, int(self._halo_a * 1.5 * self._core_flicker)))
        p.setPen(QtGui.QPen(tor_col2, 2))
        p.drawEllipse(QtCore.QPoint(cx, cy), int(tor_rb * 0.85), int(tor_rb * 0.85))

        # Plasma rings expanding
        for pr_ring in self._plasma_rings:
            pr_fr = (pr_ring - self._r * 0.25) / (self._r * 0.85)
            pr_a  = max(0, int(180 * (1.0 - pr_fr) * self._core_flicker))
            p.setPen(QtGui.QPen(self._c(*rgb, pr_a), 1.5))
            p.drawEllipse(QtCore.QPoint(cx, cy), int(pr_ring), int(pr_ring))

        # ── 7. Core glow ──────────────────────────────────────────────────
        core_r  = int(r * 0.22 * sc)
        pulse_b = 0.84 + 0.16 * math.sin(self._reactor_pulse)
        core_rp = int(core_r * pulse_b * self._core_flicker)

        # Core outer glow
        core_glow_grad = QtGui.QRadialGradient(float(cx), float(cy), float(core_rp * 2.2))
        ar_, ag_, ab_ = rgb
        core_glow_grad.setColorAt(0.0, self._c(ar_, ag_, ab_, int(60 * self._core_flicker)))
        core_glow_grad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QBrush(core_glow_grad))
        p.drawEllipse(QtCore.QPoint(cx, cy), int(core_rp * 2.2), int(core_rp * 2.2))

        # Core body
        core_grad = QtGui.QRadialGradient(float(cx), float(cy), float(core_rp))
        core_grad.setColorAt(0.0,  QtGui.QColor("#FFFFFF"))
        core_grad.setColorAt(0.12, QtGui.QColor(t["primary"]).lighter(200))
        core_grad.setColorAt(0.35, QtGui.QColor(t["primary"]).lighter(140))
        core_grad.setColorAt(0.65, QtGui.QColor(t["primary"]))
        core_grad.setColorAt(0.85, QtGui.QColor(t["secondary"]).darker(50))
        core_grad.setColorAt(1.0,  QtGui.QColor(t["dimmer"]))
        p.setBrush(QtGui.QBrush(core_grad))
        p.drawEllipse(QtCore.QPoint(cx, cy), core_rp, core_rp)

        # Core border
        c_border = QtGui.QColor(t["primary"])
        safe_set_alpha(c_border, min(255, int(self._halo_a * 3.2 * self._core_flicker)))
        p.setPen(QtGui.QPen(c_border, 3))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawEllipse(QtCore.QPoint(cx, cy), core_rp, core_rp)

        # ── 8. Lightning bolts ─────────────────────────────────────────────
        for bolt in self._bolt_pts:
            pts_b, width_b, alpha_b, rb, gb, bb = bolt
            col = self._c(rb, gb, bb, int(alpha_b))
            # Glow pass
            p.setPen(QtGui.QPen(self._c(rb, gb, bb, int(alpha_b * 0.3)), max(2, width_b / 25)))
            for i in range(len(pts_b) - 1):
                p.drawLine(QtCore.QPointF(*pts_b[i]), QtCore.QPointF(*pts_b[i + 1]))
            # Sharp pass
            p.setPen(QtGui.QPen(col, max(1, width_b / 55)))
            for i in range(len(pts_b) - 1):
                p.drawLine(QtCore.QPointF(*pts_b[i]), QtCore.QPointF(*pts_b[i + 1]))

        # ── 9. Arc sparks (high energy) ────────────────────────────────────
        if self._speaking or self._halo_a > 90:
            arc_cnt = 10 if self._speaking else 5
            for i in range(arc_cnt):
                phase = self._arc_phase + i * (2 * math.pi / arc_cnt)
                r1_   = core_rp
                r2_   = int(r * 0.6 * sc)
                steps_ = 9
                prev  = None
                for s in range(steps_ + 1):
                    fr2  = s / steps_
                    cr_  = r1_ + (r2_ - r1_) * fr2
                    jit2 = math.sin(phase * 3 + fr2 * 9) * 7 * (1 - fr2)
                    ang_ = phase + jit2 * 0.055
                    pt_  = QtCore.QPointF(
                        cx + cr_ * math.cos(ang_),
                        cy + cr_ * math.sin(ang_),
                    )
                    if prev:
                        arc_a = int(max(0, self._halo_a * 1.3) * (1 - fr2 * 0.6) * self._core_flicker)
                        p.setPen(QtGui.QPen(self._c(*rgb, arc_a), 1.5))
                        p.drawLine(prev, pt_)
                    prev = pt_

        # ── 10. Charge indicator arc ───────────────────────────────────────
        if self._reactor_charge > 0.05:
            chg_r = int(r * 0.96)
            chg_a = int(180 * self._reactor_charge)
            chg_col = QtGui.QColor(t["gold"])
            safe_set_alpha(chg_col, chg_a)
            p.setPen(QtGui.QPen(chg_col, 3))
            p.drawArc(
                QtCore.QRectF(cx - chg_r, cy - chg_r, chg_r * 2, chg_r * 2),
                90 * 16,
                int(-self._reactor_charge * 360 * 16)
            )

        # ── 11. Scan sweep ─────────────────────────────────────────────────
        scan_r = int(r * 0.97)
        sa_    = min(255, int(self._halo_a * 1.6))
        for sw_ext in [60, 40, 20]:
            sa_sw2 = int(sa_ * (sw_ext / 60) * 0.8)
            p.setPen(QtGui.QPen(self._c(*rgb, sa_sw2), 2))
            p.drawArc(
                QtCore.QRectF(cx - scan_r, cy - scan_r, scan_r * 2, scan_r * 2),
                int(-self._scan_angle * 16), int(-sw_ext * 16)
            )

        self._paint_pulse_rings(p, rgb)
        self._paint_shared_particles(p)
        self._paint_energy_pulse(p, rgb)

    # ═════════════════════════════════════════════════════════════════════════
    # AMETHYST ORB (fallback)
    # ═════════════════════════════════════════════════════════════════════════
    def _paint_orb(self, p: QtGui.QPainter, t: dict) -> None:
        cx, cy, r = self._cx, self._cy, self._r
        rgb = self._get_state_rgb(t)
        sc  = self._scale

        for i in range(8, 0, -1):
            fr  = i / 8
            hr_ = int(r * (1.04 + fr * 0.28))
            ha_ = max(0, int(self._halo_a * 0.12 * fr))
            p.setPen(QtGui.QPen(self._c(*rgb, ha_), 2))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QtCore.QPoint(cx, cy), hr_, hr_)

        for idx, rfrac in enumerate([0.92, 0.80, 0.68]):
            rr3 = int(r * rfrac)
            col = self._c(*rgb, max(0, int(self._halo_a * (0.8 - idx * 0.22))))
            p.setPen(QtGui.QPen(col, 2))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            rect3 = QtCore.QRectF(cx - rr3, cy - rr3, rr3 * 2, rr3 * 2)
            base3 = self._rings_spin[idx]
            for s in range(5):
                start3 = (base3 + s * 72) % 360
                p.drawArc(rect3, int(-start3 * 16), int(-48 * 16))

        aura_breathe = 0.91 + 0.09 * math.sin(self._orb_aura)
        orb_r = int(r * 0.44 * sc * aura_breathe)
        orb_grad = QtGui.QRadialGradient(float(cx), float(cy), float(orb_r))
        orb_grad.setColorAt(0.0, QtGui.QColor(t["primary"]).lighter(180))
        orb_grad.setColorAt(0.25, QtGui.QColor(t["primary"]).lighter(120))
        orb_grad.setColorAt(0.5, QtGui.QColor(t["primary"]))
        orb_grad.setColorAt(0.78, QtGui.QColor(t["accent2"]).darker(60))
        orb_grad.setColorAt(1.0, QtGui.QColor(t["dimmer"]))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QBrush(orb_grad))
        p.drawEllipse(QtCore.QPoint(cx, cy), orb_r, orb_r)

        p.setPen(self._c(*rgb, min(255, int(self._halo_a * 2.2))))
        f = QtGui.QFont(t["font_title"], 11, QtGui.QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(QtCore.QRect(0, cy - 12, self._size, 24),
                   QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)

        self._paint_pulse_rings(p, rgb)
        self._paint_shared_particles(p)
        self._paint_energy_pulse(p, rgb)

    # ── Shared sub-renders ─────────────────────────────────────────────────
    def _paint_pulse_rings(self, p: QtGui.QPainter, rgb: tuple) -> None:
        for pr in self._pulse_rings:
            pa = max(0, int(200 * (1.0 - pr / (self._r * 1.18))))
            p.setPen(QtGui.QPen(self._c(*rgb, pa), 2))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawEllipse(QtCore.QPoint(self._cx, self._cy), int(pr), int(pr))

    def _paint_shared_particles(self, p: QtGui.QPainter) -> None:
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        for pt in self._particles:
            # Draw trail
            if 'trail' in pt and len(pt['trail']) > 1:
                for ti in range(len(pt['trail']) - 1):
                    ta = int(pt['alpha'] * (ti / len(pt['trail'])) * 0.5)
                    tc = QtGui.QColor(pt['r'], pt['g'], pt['b'])
                    safe_set_alpha(tc, ta)
                    p.setPen(QtGui.QPen(tc, max(0.5, pt['size'] * 0.3)))
                    p.drawLine(
                        QtCore.QPointF(*pt['trail'][ti]),
                        QtCore.QPointF(*pt['trail'][ti+1])
                    )
                p.setPen(QtCore.Qt.PenStyle.NoPen)
            col = QtGui.QColor(pt['r'], pt['g'], pt['b'])
            safe_set_alpha(col, int(pt['alpha']))
            p.setBrush(col)
            sz = pt['size'] * 0.5
            p.drawEllipse(QtCore.QPointF(pt['x'], pt['y']), sz, sz)

    def _paint_energy_pulse(self, p: QtGui.QPainter, rgb: tuple) -> None:
        if self._energy_pulse > 0:
            pr2 = int(self._energy_pulse * 4.2)
            pa2 = max(0, int(self._energy_pulse * 9))
            if pr2 > 0:
                p.setPen(QtGui.QPen(self._c(*rgb, pa2), 3))
                p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
                p.drawEllipse(QtCore.QPoint(self._cx, self._cy), pr2, pr2)

    # ── Events ────────────────────────────────────────────────────────────
    def enterEvent(self, event: QtCore.QEvent) -> None:
        self._hovered = True
        self._interaction_glow = 0.8
        self.hover_changed.emit(True)
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        self._hovered = False
        self.hover_changed.emit(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self.right_clicked.emit()
            self._spell_cast = 80.0
            return
        self._pressed      = True
        self._energy_pulse = 36.0
        self._target_scale = 1.16
        self._click_flash  = 1.0
        self._interaction_glow = 1.0
        self.clicked.emit()
        _click_ripples.append([
            float(event.position().x()) + self.x(),
            float(event.position().y()) + self.y(),
            0.0
        ])
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self._pressed      = False
        self._target_scale = 1.08 if self._speaking else 1.0
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QtWidgets.QGraphicsSceneWheelEvent) -> None:
        # Scroll wheel changes animation intensity
        global _animation_intensity
        delta = event.angleDelta().y()
        _animation_intensity = max(0.2, min(2.0, _animation_intensity + delta * 0.0005))
        super().wheelEvent(event)


# ═══════════════════════════════════════════════════════════════════════════════
# HUD CORNER DECORATION
# ═══════════════════════════════════════════════════════════════════════════════
def draw_corner_bracket(
    p: QtGui.QPainter, x: int, y: int, w: int, h: int,
    color: str, alpha: int, flip_x: bool = False, flip_y: bool = False,
    thickness: int = 2
) -> None:
    arm = 26
    col = make_col(color, alpha)
    p.setPen(QtGui.QPen(col, thickness))
    sx = -1 if flip_x else 1
    sy = -1 if flip_y else 1
    # Main bracket lines
    p.drawLine(x, y, x + sx * arm, y)
    p.drawLine(x, y, x, y + sy * arm)
    # Secondary shorter lines for depth
    col2 = make_col(color, alpha // 2)
    p.setPen(QtGui.QPen(col2, 1))
    p.drawLine(x + sx * 4, y + sy * 1, x + sx * arm, y + sy * 1)
    p.drawLine(x + sx * 1, y + sy * 4, x + sx * 1, y + sy * arm)
    # Corner dot
    dot_col = make_col(color, alpha * 3 // 2)
    p.setPen(dot_col)
    p.setBrush(dot_col)
    p.drawEllipse(QtCore.QPointF(x + sx * 3, y + sy * 3), 2.5, 2.5)


# ═══════════════════════════════════════════════════════════════════════════════
# ANIMATED WAVEFORM WIDGET
# ═══════════════════════════════════════════════════════════════════════════════
class WaveformWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tick = 0
        self._speaking = False
        self._muted    = False
        self._bars = 52
        self._bar_heights = [0.0] * self._bars
        self._target_heights = [0.0] * self._bars
        self.setMinimumHeight(36)

    def set_speaking(self, v: bool):
        self._speaking = v

    def set_muted(self, v: bool):
        self._muted = v

    def tick(self):
        self._tick += 1
        t = T()
        # Update target heights
        for i in range(self._bars):
            if self._muted:
                self._target_heights[i] = 1.0
            elif self._speaking:
                self._target_heights[i] = random.uniform(4, 28)
            else:
                self._target_heights[i] = 3 + 3 * math.sin(self._tick * 0.07 + i * 0.55)
        # Smooth
        for i in range(self._bars):
            self._bar_heights[i] += (self._target_heights[i] - self._bar_heights[i]) * 0.25
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        t = T()
        W = self.width()
        H = self.height()
        bw = W / self._bars
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        max_h = H - 4
        for i in range(self._bars):
            hb = min(max_h, self._bar_heights[i])
            frac = hb / max_h
            if self._muted:
                col = make_col(t["muted_col"], 180)
            elif self._speaking:
                sr, sg, sb = t["speak_rgb"]
                col = make_rgb(
                    int(sr * frac + 255 * (1-frac) * 0.15),
                    int(sg * frac),
                    sb, 230
                )
            else:
                col = make_col(t["dim"], 160)
            p.setBrush(col)
            bx = int(i * bw) + 1
            by = int((H - hb) / 2)
            p.drawRoundedRect(bx, by, int(bw) - 1, int(hb), 1, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN UI
# ═══════════════════════════════════════════════════════════════════════════════
class OminiUI(QtWidgets.QWidget):
    log_requested      = QtCore.Signal(str)
    state_requested    = QtCore.Signal(str)
    persona_changed    = QtCore.Signal(str)
    voice_changed      = QtCore.Signal(str)
    live_voice_changed = QtCore.Signal(str)

    def __init__(self, face_path: str, size: tuple[int, int] | None = None) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwarenessContext(2)
            except Exception:
                pass
            self._app = QtWidgets.QApplication(sys.argv)
        else:
            self._app = app

        super().__init__()
        self.setWindowTitle("OMINI ASSISTANT V3")
        self.setWindowFlags(
            self.windowFlags() & ~QtCore.Qt.WindowType.WindowMaximizeButtonHint
        )

        screen = QtGui.QGuiApplication.primaryScreen()
        sg     = screen.availableGeometry() if screen else QtCore.QRect(0, 0, 1366, 768)
        W, H   = min(sg.width(), 1040), min(sg.height(), 840)
        if size:
            W, H = size
        self.resize(W, H)
        self.setMinimumSize(W, H)
        self.setMaximumSize(W, H)
        self.W, self.H = W, H

        geo = self.frameGeometry()
        geo.moveCenter(sg.center())
        self.move(geo.topLeft())

        # State
        self.speaking       = False
        self.muted          = False
        self._omini_state   = "INITIALISING"
        self._prev_state    = ""
        self.status_blink   = True
        self._start_time    = time.time()
        self._messages_sent = 0
        self._screen_shake  = 0
        self._shake_dx      = 0
        self._shake_dy      = 0
        self.on_text_command = None
        self._api_key_ready  = False
        self._face_pixmap: QtGui.QPixmap | None = None
        self._has_face       = False

        # Tooltip state
        self._tooltip_text  = ""
        self._tooltip_alpha = 0.0
        self._tooltip_pos   = QtCore.QPointF(0, 0)

        # Managers
        self._persona_manager    = get_persona_manager()    if _PERSONA_AVAILABLE    else None
        self._voice_manager      = get_voice_manager()      if _VOICE_AVAILABLE      else None
        self._live_voice_manager = get_live_voice_manager() if _LIVE_VOICE_AVAILABLE else None
        self._selected_persona    = (
            self._persona_manager.get_selected_key()    if self._persona_manager    else "executive"
        )
        self._selected_voice      = (
            self._voice_manager.get_selected_key()      if self._voice_manager      else "en_us-danny-low"
        )
        self._selected_live_voice = (
            self._live_voice_manager.get_selected_key() if self._live_voice_manager else "Charon"
        )

        self._load_face(face_path)

        # Typing
        self.typing_queue: deque[str] = deque()
        self.is_typing     = False
        self._typing_text  = ""
        self._typing_idx   = 0
        self._typing_color = QtGui.QColor("#C4A8FF")

        # Background FX state
        self._hex_phase     = 0.0
        self._data_chars:   list[dict] = []
        self._bg_particles: list[dict] = []
        self._tick          = 0
        self._last_frame_t  = time.time()
        self._corner_pulse  = 0.0
        self._hud_scroll    = 0.0
        self._scanline_y    = 0.0   # scanline CRT effect
        self._vignette_a    = 0.0   # vignette pulse

        self.setAutoFillBackground(True)
        self.setMouseTracking(True)
        self._apply_bg_palette()
        self._build_ui()

        self.log_requested.connect(self._enqueue_log)
        self.state_requested.connect(self._set_state_impl)

        self._api_key_ready = self._api_keys_exist()
        if not self._api_key_ready:
            QtCore.QTimer.singleShot(10, self._show_setup_ui)

        self._anim_timer = QtCore.QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(16)

        QtGui.QShortcut(QtGui.QKeySequence("F4"), self, activated=self._toggle_mute)
        QtGui.QShortcut(QtGui.QKeySequence("F5"), self, activated=self._cycle_theme)
        QtGui.QShortcut(QtGui.QKeySequence("F11"), self, activated=self.toggle_fullscreen)

    def _apply_bg_palette(self) -> None:
        t = T()
        pal = self.palette()
        pal.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(t["bg"]))
        self.setPalette(pal)

    def run(self) -> int:
        self.show()
        return self._app.exec()

    def _load_face(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            return
        pix = QtGui.QPixmap(str(p))
        if not pix.isNull():
            self._face_pixmap = pix
            self._has_face    = True

    # ═════════════════════════════════════════════════════════════════════════
    # UI BUILD
    # ═════════════════════════════════════════════════════════════════════════
    def _build_ui(self) -> None:
        t  = T()
        W, H = self.W, self.H

        # Central orb
        ORB_SZ = min(int(H * 0.50), 390)
        orb_x  = (W - ORB_SZ) // 2
        orb_y  = int(H * 0.115)
        self._orb_widget = CentralOrbWidget(ORB_SZ, self)
        self._orb_widget.setGeometry(orb_x, orb_y, ORB_SZ, ORB_SZ)
        self._orb_widget.clicked.connect(self._orb_clicked)
        self._orb_widget.right_clicked.connect(self._orb_right_clicked)
        self._orb_widget.hover_changed.connect(self._on_orb_hover)
        self._ORB_SZ    = ORB_SZ
        self._orb_y     = orb_y
        # Orb hover tooltip (simple preview & instructions)
        self._orb_tooltip = QtWidgets.QLabel(self)
        self._orb_tooltip.setStyleSheet(f"""
            QLabel {{ background: rgba(0,0,0,160); color: {T()['text']};
                border: 1px solid {T()['dim']}; padding: 8px; border-radius: 8px;
                font-family: 'Courier New'; font-size: 9pt;
            }}
        """)
        self._orb_tooltip.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._orb_tooltip.hide()

        # ── Left panel: selectors ─────────────────────────────────────────
        self._selector_widgets: list[QtWidgets.QWidget] = []
        LEFT_X  = 14
        LEFT_W  = int(W * 0.155)

        y_off = 90
        for cap, battr, lister, selattr, default, slot in [
            ("PERSONA",    "_persona_box",    list_personas,    "_selected_persona",     "executive",       "_on_persona_changed"),
            ("VOICE",      "_voice_box",       list_voices,      "_selected_voice",       "en_us-danny-low", "_on_voice_changed"),
            ("LIVE VOICE", "_live_voice_box",  list_live_voices, "_selected_live_voice",  "Charon",          "_on_live_voice_changed"),
        ]:
            lbl = self._make_label(cap, self)
            lbl.setGeometry(LEFT_X, y_off, LEFT_W, 15)
            y_off += 17
            box = self._make_combo(self)
            box.setGeometry(LEFT_X, y_off, LEFT_W, 26)
            for item in lister():
                box.addItem(item.title, item.key)
            idx = box.findData(getattr(self, selattr))
            if idx >= 0:
                box.setCurrentIndex(idx)
            box.currentIndexChanged.connect(getattr(self, slot))
            setattr(self, battr, box)
            self._selector_widgets.extend([lbl, box])
            y_off += 34

        # ── Log frame ─────────────────────────────────────────────────────
        LOG_W = int(W * 0.66)
        LOG_H = 114
        LOG_Y = H - LOG_H - 90
        LOG_X = (W - LOG_W) // 2

        self.log_frame = QtWidgets.QFrame(self)
        self.log_frame.setGeometry(LOG_X, LOG_Y, LOG_W, LOG_H)
        self._style_log_frame()

        self.log_text = QtWidgets.QTextEdit(self.log_frame)
        self.log_text.setGeometry(0, 0, LOG_W, LOG_H)
        self.log_text.setReadOnly(True)
        self._style_log_text()

        # ── Waveform widget ────────────────────────────────────────────────
        self._waveform = WaveformWidget(self)
        WF_Y = LOG_Y - 44
        self._waveform.setGeometry(LOG_X, WF_Y, LOG_W, 38)
        self._waveform.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        # ── Input row ─────────────────────────────────────────────────────
        INP_Y = LOG_Y + LOG_H + 7
        BTN_W = 90
        INP_W = LOG_W - BTN_W - 7

        self._input = QtWidgets.QLineEdit(self)
        self._input.setGeometry(LOG_X, INP_Y, INP_W, 35)
        self._input.setPlaceholderText("Issue command to neural core…")
        self._style_input()
        self._input.returnPressed.connect(self._on_input_submit)

        self._send_btn = QtWidgets.QPushButton("SEND ▸", self)
        self._send_btn.setGeometry(LOG_X + INP_W + 7, INP_Y, BTN_W, 35)
        self._send_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._style_send_btn()
        self._send_btn.clicked.connect(self._on_input_submit)

        # ── Bottom action row ──────────────────────────────────────────────
        BTN_Y = H - 44

        self._mute_btn = QtWidgets.QPushButton(self)
        self._mute_btn.setGeometry(14, BTN_Y, 130, 32)
        self._mute_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._mute_btn.clicked.connect(self._toggle_mute)
        self._draw_mute_button()

        # Theme switcher buttons
        THEME_BTN_W = 112
        THEME_GAP   = 6
        THEME_TOTAL = len(THEMES) * THEME_BTN_W + (len(THEMES) - 1) * THEME_GAP
        theme_start_x = W - THEME_TOTAL - 14
        self._theme_btns: list[tuple[QtWidgets.QPushButton, str]] = []
        for i, (key, td) in enumerate(THEMES.items()):
            btn = QtWidgets.QPushButton(td["name"], self)
            bx  = theme_start_x + i * (THEME_BTN_W + THEME_GAP)
            btn.setGeometry(bx, BTN_Y, THEME_BTN_W, 32)
            btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _chk=False, k=key: self.set_theme(k))
            self._theme_btns.append((btn, key))
            self._style_theme_btn(btn, key)

        # Clear log micro button
        clr = QtWidgets.QPushButton("CLR", self)
        clr.setGeometry(LOG_X + LOG_W - 38, LOG_Y - 22, 38, 20)
        clr.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        clr.setStyleSheet(f"""
            QPushButton {{
                color: {t['dim']}; background: transparent;
                border: 1px solid {t['dim']}; border-radius: 4px;
                font-family: 'Courier New'; font-size: 7pt;
            }}
            QPushButton:hover {{ color: {t['text']}; border-color: {t['secondary']}; }}
        """)
        clr.clicked.connect(self.log_text.clear)

    # ── Widget style helpers ──────────────────────────────────────────────
    def _make_label(self, text: str, parent: QtWidgets.QWidget) -> QtWidgets.QLabel:
        lbl = QtWidgets.QLabel(text, parent)
        t   = T()
        lbl.setStyleSheet(f"""
            QLabel {{
                color: {t['dim']}; font-family: 'Courier New', monospace;
                font-size: 7pt; font-weight: 700; letter-spacing: 2px;
                background: transparent;
            }}
        """)
        return lbl

    def _make_combo(self, parent: QtWidgets.QWidget) -> QtWidgets.QComboBox:
        t   = T()
        box = QtWidgets.QComboBox(parent)
        box.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        box.setStyleSheet(f"""
            QComboBox {{
                color: {t['text']}; background: {t['dimmer']};
                border: 1px solid {t['dim']}; border-radius: 6px;
                padding-left: 8px; font-family: 'Courier New', monospace; font-size: 8pt;
            }}
            QComboBox::drop-down {{ border: 0; width: 16px; }}
            QComboBox QAbstractItemView {{
                background: {t['panel']}; color: {t['text']};
                selection-background-color: {t['dim']};
                border: 1px solid {t['secondary']};
            }}
        """)
        return box

    def _style_log_frame(self) -> None:
        t = T()
        self.log_frame.setStyleSheet(f"""
            QFrame {{
                background: {t['panel']}; border: 1px solid {t['dim']};
                border-radius: 10px;
            }}
        """)

    def _style_log_text(self) -> None:
        t = T()
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                color: {t['text']}; background: transparent; border: 0;
                font-family: 'Courier New', monospace; font-size: 10pt;
                padding: 8px 12px;
            }}
            QScrollBar:vertical {{
                background: {t['dimmer']}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {t['dim']}; border-radius: 3px;
            }}
        """)

    def _style_input(self) -> None:
        t = T()
        self._input.setStyleSheet(f"""
            QLineEdit {{
                color: {t['text']}; background: {t['dimmer']};
                border: 1px solid {t['dim']}; border-radius: 8px;
                padding-left: 12px; font-family: 'Courier New', monospace; font-size: 10pt;
            }}
            QLineEdit:focus {{ border: 1px solid {t['secondary']}; background: {t['panel']}; }}
        """)

    def _style_send_btn(self) -> None:
        t = T()
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                color: {t['primary']}; background: {t['dimmer']};
                border: 1px solid {t['secondary']}; border-radius: 8px;
                font-family: 'Courier New', monospace; font-size: 9pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: {t['dim']}; color: {t['gold']}; }}
            QPushButton:pressed {{ background: {t['panel']}; }}
        """)

    def _style_theme_btn(self, btn: QtWidgets.QPushButton, key: str) -> None:
        t_cur  = T()
        t_this = THEMES[key]
        active = (key == _current_theme)
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {t_this['secondary']}; color: {t_this['primary']};
                    border: 2px solid {t_this['primary']}; border-radius: 8px;
                    font-family: 'Courier New', monospace; font-size: 8pt; font-weight: 700;
                    letter-spacing: 1px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {t_cur['dimmer']}; color: {t_cur['dim']};
                    border: 1px solid {t_cur['dim']}; border-radius: 8px;
                    font-family: 'Courier New', monospace; font-size: 8pt; font-weight: 700;
                    letter-spacing: 1px;
                }}
                QPushButton:hover {{
                    color: {t_this['primary']}; border-color: {t_this['secondary']};
                    background: {t_cur['panel']};
                }}
            """)

    def _draw_mute_button(self) -> None:
        t = T()
        if self.muted:
            self._mute_btn.setText("● MUTED")
            self._mute_btn.setStyleSheet(f"""
                QPushButton {{
                    color: {t['muted_col']}; background: {t['dimmer']};
                    border: 1px solid {t['muted_col']}; border-radius: 8px;
                    font-family: 'Courier New', monospace; font-size: 10pt; font-weight: 700;
                }}
                QPushButton:hover {{ background: {t['dim']}; }}
            """)
        else:
            self._mute_btn.setText("◉ LIVE")
            self._mute_btn.setStyleSheet(f"""
                QPushButton {{
                    color: {t['green']}; background: {t['panel']};
                    border: 1px solid {t['dim']}; border-radius: 8px;
                    font-family: 'Courier New', monospace; font-size: 10pt; font-weight: 700;
                }}
                QPushButton:hover {{ background: {t['dim']}; }}
            """)

    # ═════════════════════════════════════════════════════════════════════════
    # ANIMATION TICK
    # ═════════════════════════════════════════════════════════════════════════
    def _animate(self) -> None:
        self._tick += 1
        t = T()

        self._hex_phase   = (self._hex_phase + 0.022 * _animation_intensity) % (2 * math.pi)
        self._corner_pulse = (self._corner_pulse + 0.04) % (math.pi * 2)
        self._hud_scroll   = (self._hud_scroll   + 0.5 * _animation_intensity) % 200
        self._scanline_y   = (self._scanline_y   + 1.8) % max(1, self.H)
        self._vignette_a   = 0.5 + 0.5 * math.sin(self._hex_phase * 0.5)

        if self._tick % 38 == 0:
            self.status_blink = not self.status_blink

        # BG ambient particles
        if self._tick % 7 == 0 and _animation_intensity > 0.35:
            pr, pg, pb = t["particle_col"]
            self._bg_particles.append({
                'x': random.uniform(0, self.W),
                'y': self.H + 5,
                'vx': random.uniform(-0.35, 0.35),
                'vy': random.uniform(-0.7, -0.12),
                'alpha': 70,
                'size': random.uniform(1.0, 3.0),
                'r': pr, 'g': pg, 'b': pb,
            })
        for pt in self._bg_particles[:]:
            pt['x']     += pt['vx']
            pt['y']     += pt['vy']
            pt['alpha'] -= 1
            if pt['alpha'] <= 0:
                self._bg_particles.remove(pt)

        # Orbiting data chars around the central orb
        orb_cx = self.W // 2
        orb_cy = self._orb_y + self._ORB_SZ // 2
        orb_r2 = self._ORB_SZ // 2

        if self._tick % 5 == 0 and random.random() < 0.3 * _animation_intensity:
            is_hog = (_current_theme == "hogwarts")
            chars  = list(RUNE_CHARS) if is_hog else list(LATIN_RUNES)
            self._data_chars.append({
                'char':  random.choice(chars),
                'angle': random.uniform(0, 360),
                'dist':  orb_r2 * 1.12 + random.uniform(-4, 4),
                'speed': random.uniform(0.3, 1.3) * _animation_intensity,
                'alpha': 140,
                'cx': orb_cx, 'cy': orb_cy,
            })
        for ds in self._data_chars[:]:
            ds['angle']  = (ds['angle'] + ds['speed']) % 360
            ds['alpha']  = max(0, ds['alpha'] - 4)
            if ds['alpha'] <= 0:
                self._data_chars.remove(ds)

        # Waveform
        if hasattr(self, '_waveform'):
            self._waveform.set_speaking(self.speaking)
            self._waveform.set_muted(self.muted)
            self._waveform.tick()

        self._orb_widget.tick()
        self.update()

    # ═════════════════════════════════════════════════════════════════════════
    # PAINT EVENT
    # ═════════════════════════════════════════════════════════════════════════
    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)

        t  = T()
        W, H   = self.W, self.H
        orb_cx = W // 2
        orb_cy = self._orb_y + self._ORB_SZ // 2
        orb_r2 = self._ORB_SZ // 2

        # Screen shake transform
        if self._screen_shake > 0:
            self._shake_dx = random.randint(-self._screen_shake, self._screen_shake)
            self._shake_dy = random.randint(-self._screen_shake, self._screen_shake)
            self._screen_shake = max(0, self._screen_shake - 1)
        else:
            self._shake_dx = 0
            self._shake_dy = 0
        painter.translate(self._shake_dx, self._shake_dy)

        # ── 1. Background ─────────────────────────────────────────────────
        painter.fillRect(self.rect(), QtGui.QColor(t["bg"]))

        # Radial ambient glow from orb center
        center_glow = QtGui.QRadialGradient(float(orb_cx), float(orb_cy), float(orb_r2 * 2.4))
        glow_rgb = t["listen_rgb"]
        center_glow.setColorAt(0.0, make_rgb(*glow_rgb, int(22 + 12 * math.sin(self._hex_phase))))
        center_glow.setColorAt(0.5, make_rgb(*glow_rgb, int(8 + 4 * math.sin(self._hex_phase))))
        center_glow.setColorAt(1.0, QtGui.QColor(t["bg"]))
        painter.fillRect(self.rect(), center_glow)

        # ── 2. Vignette ───────────────────────────────────────────────────
        vign_grad = QtGui.QRadialGradient(float(W/2), float(H/2), float(max(W, H) * 0.72))
        vign_grad.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
        vign_grad.setColorAt(0.65, QtGui.QColor(0, 0, 0, 0))
        vign_grad.setColorAt(1.0,  QtGui.QColor(0, 0, 0, int(120 + 30 * self._vignette_a)))
        painter.fillRect(self.rect(), vign_grad)

        # ── 3. BG particles ───────────────────────────────────────────────
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        for pt in self._bg_particles:
            col = QtGui.QColor(pt['r'], pt['g'], pt['b'])
            safe_set_alpha(col, pt['alpha'])
            painter.setBrush(col)
            painter.drawEllipse(QtCore.QPointF(pt['x'], pt['y']), pt['size'], pt['size'])

        # ── 4. Background grid ────────────────────────────────────────────
        self._draw_bg_grid(painter, t, W, H, orb_cx, orb_cy, orb_r2)

        # ── 5. Scanline effect (subtle CRT) ───────────────────────────────
        if _current_theme == "avengers" or _current_theme == "amethyst":
            scan_col = QtGui.QColor(*t["listen_rgb"])
            safe_set_alpha(scan_col, 8)
            for sy in range(0, H, 4):
                painter.setPen(QtGui.QPen(scan_col, 1))
                painter.drawLine(0, sy, W, sy)

        # ── 6. Orbiting data characters ───────────────────────────────────
        painter.setFont(QtGui.QFont("Courier New", 7))
        for ds in self._data_chars:
            rad = math.radians(ds['angle'])
            dx  = ds['cx'] + ds['dist'] * math.cos(rad)
            dy  = ds['cy'] + ds['dist'] * math.sin(rad)
            col = QtGui.QColor(*t["particle_col"])
            safe_set_alpha(col, ds['alpha'])
            painter.setPen(col)
            painter.drawText(int(dx) - 3, int(dy) + 4, ds['char'])

        # ── 7. Header bar ─────────────────────────────────────────────────
        self._draw_header(painter, t, W, H)

        # ── 8. Status + waveform is drawn by widget, just status text ─────
        self._draw_status_row(painter, t, W, orb_cy, orb_r2)

        # ── 9. Footer bar ─────────────────────────────────────────────────
        self._draw_footer(painter, t, W, H)

        # ── 10. HUD (right side stats) ────────────────────────────────────
        self._draw_right_hud(painter, t, W, H)

        # ── 11. Left panel separator line ─────────────────────────────────
        panel_w = int(W * 0.162)
        sep_grad = QtGui.QLinearGradient(float(panel_w), 80.0, float(panel_w), float(H - 50))
        sep_grad.setColorAt(0.0, QtGui.QColor(t["bg"]))
        sep_grad.setColorAt(0.3, QtGui.QColor(t["dim"]))
        sep_grad.setColorAt(0.7, QtGui.QColor(t["dim"]))
        sep_grad.setColorAt(1.0, QtGui.QColor(t["bg"]))
        painter.setPen(QtGui.QPen(QtGui.QBrush(sep_grad), 1))
        painter.drawLine(panel_w, 80, panel_w, H - 50)

        # ── 12. Corner HUD brackets ───────────────────────────────────────
        ca = int(70 + 50 * math.sin(self._corner_pulse))
        for fx, fy, bx, by in [
            (False, False, 0,   0  ),
            (True,  False, W-1, 0  ),
            (False, True,  0,   H-1),
            (True,  True,  W-1, H-1),
        ]:
            draw_corner_bracket(painter, bx, by, 26, 26, t["primary"], ca, fx, fy, 2)

        # ── 13. Click ripples ─────────────────────────────────────────────
        rgb_rip = t["listen_rgb"]
        dead: list[list] = []
        for rip in _click_ripples:
            rip[2] += 2.8 * _animation_intensity
            radius  = int(rip[2] * 2.4)
            alpha   = max(0, int(240 - rip[2] * 6.0))
            if alpha <= 0:
                dead.append(rip)
                continue
            col = make_rgb(*rgb_rip, alpha)
            painter.setPen(QtGui.QPen(col, 2))
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QtCore.QPoint(int(rip[0]), int(rip[1])), radius, radius)
            # Secondary smaller ripple
            col2 = make_rgb(*rgb_rip, alpha // 3)
            painter.setPen(QtGui.QPen(col2, 1))
            painter.drawEllipse(QtCore.QPoint(int(rip[0]), int(rip[1])), radius // 2, radius // 2)
        for d in dead:
            if d in _click_ripples:
                _click_ripples.remove(d)

        # ── 14. FPS counter ───────────────────────────────────────────────
        elapsed = time.time() - self._last_frame_t
        fps_val = int(1 / elapsed) if elapsed > 0 else 0
        self._last_frame_t = time.time()
        painter.setFont(QtGui.QFont("Courier New", 7))
        painter.setPen(make_col(t["dim"], 120))
        painter.drawText(18, H - 34, f"FPS:{fps_val}")

        # ── 15. Avengers scanner sweep overlay ────────────────────────────
        if _current_theme == "avengers":
            sweep_pos = int(orb_cy - 200 + 400 * ((self._tick % 140) / 140))
            if abs(sweep_pos - orb_cy) < 220:
                sg = QtGui.QLinearGradient(0.0, float(sweep_pos), float(W), float(sweep_pos))
                sg.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
                sg.setColorAt(0.25, QtGui.QColor(0, 212, 255, 14))
                sg.setColorAt(0.5,  QtGui.QColor(0, 212, 255, 40))
                sg.setColorAt(0.75, QtGui.QColor(0, 212, 255, 14))
                sg.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
                painter.fillRect(QtCore.QRect(0, sweep_pos - 1, W, 3), sg)

        # ── 16. Hogwarts floating particles ──────────────────────────────
        if _current_theme == "hogwarts":
            # Draw golden dust motes
            if not hasattr(self, '_motes'):
                self._motes = [
                    {'x': random.uniform(0, W), 'y': random.uniform(0, H),
                     'vy': random.uniform(-0.3, -0.05), 'vx': random.uniform(-0.1, 0.1),
                     'alpha': random.randint(20, 80), 'size': random.uniform(1, 2.5),
                     'phase': random.uniform(0, math.pi * 2)}
                    for _ in range(60)
                ]
            for m in self._motes:
                m['y'] += m['vy']
                m['x'] += m['vx'] + 0.2 * math.sin(self._hex_phase + m['phase'])
                m['phase'] += 0.02
                if m['y'] < -5:
                    m['y'] = H + 5
                    m['x'] = random.uniform(0, W)
                gold = QtGui.QColor(201, 162, 39, int(m['alpha'] * (0.6 + 0.4 * math.sin(m['phase']))))
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(gold)
                painter.drawEllipse(QtCore.QPointF(m['x'], m['y']), m['size'], m['size'])

    # ── Sub-draw helpers ──────────────────────────────────────────────────
    def _draw_bg_grid(self, p: QtGui.QPainter, t: dict, W: int, H: int,
                      fcx: int, fcy: int, orb_r: int) -> None:
        if _current_theme == "hogwarts":
            # Star field — twinkling dots with depth
            hsx, hsy = 52, 46
            for row in range(H // hsy + 2):
                for col in range(W // hsx + 2):
                    bx = col * hsx + (hsx // 2 if row % 2 else 0)
                    by = row * hsy
                    dist = math.hypot(bx - fcx, by - fcy)
                    phase = self._hex_phase - dist * 0.009
                    bri   = max(0.0, math.sin(phase))
                    a     = max(0, min(255, int(35 * bri * _animation_intensity)))
                    c = QtGui.QColor(t["primary"])
                    safe_set_alpha(c, a)
                    p.setPen(QtCore.Qt.PenStyle.NoPen)
                    p.setBrush(c)
                    sz = 1.0 + 0.9 * bri
                    p.drawEllipse(QtCore.QPointF(bx, by), sz, sz)
            # Constellation lines
            p.setPen(QtGui.QPen(make_col(t["dim"], 15), 0.5))
            for i in range(0, len(range(H // hsy + 2)), 3):
                for j in range(0, len(range(W // hsx + 2)), 4):
                    bx1 = j * hsx + (hsx // 2 if i % 2 else 0)
                    by1 = i * hsy
                    bx2 = (j+2) * hsx + (hsx // 2 if (i+1) % 2 else 0)
                    by2 = (i+1) * hsy
                    if 0 <= bx1 < W and 0 <= by1 < H and 0 <= bx2 < W and 0 <= by2 < H:
                        p.drawLine(bx1, by1, bx2, by2)

        elif _current_theme == "avengers":
            # Circuit board grid
            grid_sz = 44
            for bx in range(0, W + grid_sz, grid_sz):
                dist = abs(bx - fcx) / (W * 0.5)
                a = max(0, int(18 * max(0, 1 - dist) * _animation_intensity))
                c = QtGui.QColor(t["primary"])
                safe_set_alpha(c, a)
                p.setPen(QtGui.QPen(c, 1))
                p.drawLine(bx, 0, bx, H)
            for by in range(0, H + grid_sz, grid_sz):
                dist = abs(by - fcy) / (H * 0.5)
                a = max(0, int(18 * max(0, 1 - dist) * _animation_intensity))
                c = QtGui.QColor(t["primary"])
                safe_set_alpha(c, a)
                p.setPen(QtGui.QPen(c, 1))
                p.drawLine(0, by, W, by)
            # Circuit traces
            p.setPen(QtGui.QPen(make_col(t["dim"], 18), 1))
            for i in range(-W, W * 2, 120):
                p.drawLine(i, 0, i + H, H)
            # Active circuit nodes
            for nxi in range(0, W, grid_sz):
                for nyi in range(0, H, grid_sz):
                    if random.random() < 0.002 * _animation_intensity:
                        nc = QtGui.QColor(t["primary"])
                        safe_set_alpha(nc, 100)
                        p.setPen(QtCore.Qt.PenStyle.NoPen)
                        p.setBrush(nc)
                        p.drawEllipse(QtCore.QPointF(nxi, nyi), 2, 2)
        else:
            # Amethyst hex dot field
            hsx, hsy = 36, 31
            for row in range(H // hsy + 2):
                for col in range(W // hsx + 2):
                    bx = col * hsx + (hsx // 2 if row % 2 else 0)
                    by = row * hsy
                    dist = math.hypot(bx - fcx, by - fcy)
                    pulse = 0.3 + 0.7 * math.sin(self._hex_phase - dist * 0.014)
                    a = max(0, min(255, int(16 * pulse * _animation_intensity)))
                    c = QtGui.QColor(t["dim"])
                    safe_set_alpha(c, a)
                    p.setPen(QtGui.QPen(c, 2))
                    p.drawPoint(bx, by)

    def _draw_header(self, p: QtGui.QPainter, t: dict, W: int, H: int) -> None:
        HDR_H = 72
        # Header gradient
        hdr_grad = QtGui.QLinearGradient(0.0, 0.0, 0.0, float(HDR_H))
        hdr_grad.setColorAt(0.0, QtGui.QColor(t["header_bg"]))
        hdr_grad.setColorAt(1.0, QtGui.QColor(t["bg"]))
        p.fillRect(0, 0, W, HDR_H, QtGui.QBrush(hdr_grad))

        # Shimmer line at bottom of header
        for xi in range(0, W, 2):
            frac = xi / W
            a_   = int(45 + 85 * abs(math.sin(frac * math.pi + self._hex_phase * 0.6)))
            c_   = QtGui.QColor(*t["listen_rgb"])
            safe_set_alpha(c_, a_)
            p.setPen(QtGui.QPen(c_, 1))
            p.drawPoint(xi, HDR_H)

        # Model badge
        p.setPen(make_col(t["dim"], 190))
        p.setFont(QtGui.QFont("Courier New", 7, QtGui.QFont.Weight.Bold))
        p.drawText(18, 30, MODEL_BADGE)

        # Main title
        is_hog = (_current_theme == "hogwarts")
        tf = QtGui.QFont(t["font_title"], 20, QtGui.QFont.Weight.Bold)
        if is_hog:
            tf.setItalic(True)
        p.setFont(tf)
        if is_hog:
            # Gold shadow for parchment depth
            for sx_, sy_, alpha_s in [(-1, 1, 30), (1, 1, 30), (0, 2, 50)]:
                p.setPen(make_col(t["accent2"], alpha_s))
                p.drawText(QtCore.QRect(sx_, 8 + sy_, W, 36),
                           QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)
            p.setPen(QtGui.QColor(t["primary"]))
            p.drawText(QtCore.QRect(0, 8, W, 36), QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)
        elif _current_theme == "avengers":
            # Stark blue glow shadow
            p.setPen(make_col(t["primary"], 40))
            p.drawText(QtCore.QRect(4, 12, W, 36), QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)
            p.setPen(make_col(t["primary"], 80))
            p.drawText(QtCore.QRect(2, 10, W, 36), QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)
            p.setPen(QtGui.QColor(t["primary"]))
            p.drawText(QtCore.QRect(0, 8, W, 36), QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)
        else:
            # Amethyst — subtle glow
            p.setPen(make_col(t["accent2"], 50))
            p.drawText(QtCore.QRect(2, 10, W, 36), QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)
            p.setPen(QtGui.QColor(t["primary"]))
            p.drawText(QtCore.QRect(0, 8, W, 36), QtCore.Qt.AlignmentFlag.AlignHCenter, SYSTEM_NAME)

        # Subtitle
        sub_f = QtGui.QFont("Courier New", 7)
        sub_f.setLetterSpacing(QtGui.QFont.SpacingType.AbsoluteSpacing, 4)
        p.setFont(sub_f)
        p.setPen(make_col(t["secondary"], 200))
        subtitles = {
            "amethyst": "DEEP SPACE NEURAL INTERFACE  ·  ARCANE FRAMEWORK  ·  QUANTUM COGNITION",
            "hogwarts":  "∗  THE ALL-SEEING ARCANE ORACLE  ·  ANCIENT MYSTICAL INTELLIGENCE  ∗",
            "avengers":  "STARK INDUSTRIES  ·  J.A.R.V.I.S  NEURAL CORE  ·  ARC REACTOR POWERED",
        }
        p.drawText(
            QtCore.QRect(0, 50, W, 18),
            QtCore.Qt.AlignmentFlag.AlignHCenter,
            subtitles.get(_current_theme, "")
        )

        # Clock (right)
        clk_f = QtGui.QFont("Courier New", 14, QtGui.QFont.Weight.Bold)
        p.setFont(clk_f)
        p.setPen(QtGui.QColor(t["primary"]))
        p.drawText(
            QtCore.QRect(0, 12, W - 20, 42),
            QtCore.Qt.AlignmentFlag.AlignRight,
            time.strftime("%H:%M:%S")
        )
        # Date
        p.setFont(QtGui.QFont("Courier New", 7))
        p.setPen(make_col(t["dim"], 160))
        p.drawText(
            QtCore.QRect(0, 54, W - 20, 16),
            QtCore.Qt.AlignmentFlag.AlignRight,
            time.strftime("%Y.%m.%d")
        )

    def _draw_status_row(self, p: QtGui.QPainter, t: dict, W: int, orb_cy: int, orb_r: int) -> None:
        sy = orb_cy + orb_r + 14

        # Status pill
        if self.muted:
            stat, sc_ = "● MUTED", t["muted_col"]
        elif self.speaking:
            sc_rgb = t["speak_rgb"]
            stat   = "◉ SPEAKING"
            sc_    = "#{:02X}{:02X}{:02X}".format(*sc_rgb)
        elif self._omini_state == "THINKING":
            stat = f"{'◈' if self.status_blink else '◇'} THINKING"
            sc_  = t["accent2"]
        elif self._omini_state == "PROCESSING":
            stat = f"{'▷' if self.status_blink else '▸'} PROCESSING"
            sc_  = t["gold"]
        elif self._omini_state == "LISTENING":
            stat = f"{'◉' if self.status_blink else '○'} LISTENING"
            sc_  = t["primary"]
        else:
            stat = f"{'●' if self.status_blink else '○'} {self._omini_state}"
            sc_  = t["primary"]

        # Status pill background
        st_font = QtGui.QFont(t["font_title"], 12, QtGui.QFont.Weight.Bold)
        p.setFont(st_font)
        fm  = p.fontMetrics()
        tw_ = fm.horizontalAdvance(stat) + 28
        pill_x = (W - tw_) // 2
        pill_bg = QtGui.QColor(t["panel"])
        safe_set_alpha(pill_bg, 160)
        pill_brd = QtGui.QColor(sc_)
        safe_set_alpha(pill_brd, 100)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(pill_bg)
        p.drawRoundedRect(pill_x, sy, tw_, 26, 13, 13)
        p.setPen(QtGui.QPen(pill_brd, 1))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(pill_x, sy, tw_, 26, 13, 13)
        p.setPen(QtGui.QColor(sc_))
        p.drawText(QtCore.QRect(0, sy, W, 26), QtCore.Qt.AlignmentFlag.AlignHCenter, stat)

    def _draw_footer(self, p: QtGui.QPainter, t: dict, W: int, H: int) -> None:
        FH = 30
        # Footer gradient
        ftr_grad = QtGui.QLinearGradient(0.0, float(H - FH), 0.0, float(H))
        ftr_grad.setColorAt(0.0, QtGui.QColor(t["bg"]))
        ftr_grad.setColorAt(1.0, QtGui.QColor(t["header_bg"]))
        p.fillRect(0, H - FH, W, FH, QtGui.QBrush(ftr_grad))
        p.setPen(QtGui.QPen(make_col(t["dim"], 80), 1))
        p.drawLine(0, H - FH, W, H - FH)
        p.setFont(QtGui.QFont("Courier New", 8))
        p.setPen(make_col(t["dim"], 140))
        p.drawText(
            QtCore.QRect(0, H - FH + 2, W - 18, FH - 4),
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter,
            "[F4] MUTE  ·  [F5] CYCLE  ·  [F11] FULLSCREEN  ·  Right-click orb for modes  ·  O.M.I.N.I v3.0"
        )

    def _draw_right_hud(self, p: QtGui.QPainter, t: dict, W: int, H: int) -> None:
        hud_x = W - 154
        hud_y = 90
        hud_w = 138
        hud_h = 130
        # HUD background
        hud_bg = QtGui.QLinearGradient(float(hud_x - 6), float(hud_y), float(hud_x + hud_w + 6), float(hud_y))
        hud_bg.setColorAt(0.0, make_col(t["panel"], 0))
        hud_bg.setColorAt(0.3, make_col(t["panel"], 90))
        hud_bg.setColorAt(1.0, make_col(t["panel"], 90))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(QtGui.QBrush(hud_bg))
        p.drawRoundedRect(hud_x - 6, hud_y - 4, hud_w + 12, hud_h, 8, 8)
        # HUD border
        p.setPen(QtGui.QPen(make_col(t["dim"], 70), 1))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(hud_x - 6, hud_y - 4, hud_w + 12, hud_h, 8, 8)

        p.setFont(QtGui.QFont("Courier New", 7))
        rows = [
            ("UPTIME",   self._get_uptime()),
            ("MSGS",     str(self._messages_sent)),
            ("THEME",    _current_theme.upper()),
            ("STATE",    self._omini_state[:9]),
            ("INTEN",    f"{_animation_intensity:.1f}x"),
            ("STATUS",   "ONLINE" if not self.muted else "MUTED"),
        ]
        for i, (lbl, val) in enumerate(rows):
            y_r = hud_y + i * 18
            p.setPen(make_col(t["dim"], 190))
            p.drawText(hud_x, y_r + 12, f"{lbl}:")
            val_col = QtGui.QColor(t["primary"]) if val == "ONLINE" else QtGui.QColor(t["text"])
            if val == "MUTED":
                val_col = QtGui.QColor(t["muted_col"])
            safe_set_alpha(val_col, 210)
            p.setPen(val_col)
            p.drawText(hud_x + 50, y_r + 12, val)

        # Signal strength bars
        sig_y = hud_y + hud_h - 22
        p.setPen(make_col(t["dim"], 150))
        p.setFont(QtGui.QFont("Courier New", 6))
        p.drawText(hud_x, sig_y + 8, "SIG:")
        for si in range(8):
            bar_h = 3 + si * 2
            bar_a = 180 if si < 6 else 80
            brc   = make_col(t["primary"], bar_a)
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(brc)
            p.drawRect(hud_x + 30 + si * 12, sig_y + 8 - bar_h, 9, bar_h)

        # Scrolling data stream
        p.setFont(QtGui.QFont("Courier New", 6))
        data_y = hud_y + hud_h + 8
        scroll_chars = "101100110101001110001011001011010"
        for row_i in range(6):
            dy_ = data_y + row_i * 12 - int(self._hud_scroll) % 72
            if dy_ < hud_y + hud_h or dy_ > H - 60:
                continue
            line = scroll_chars[(row_i * 5) % len(scroll_chars):((row_i * 5) + 18) % len(scroll_chars)]
            p.setPen(make_col(t["dim"], 50))
            p.drawText(hud_x, dy_, line)

    # ── Mouse events ──────────────────────────────────────────────────────
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        pos    = event.position().toPoint()
        orb_cx = self.W // 2
        orb_cy = self._orb_y + self._ORB_SZ // 2
        dx = (pos.x() - orb_cx) / (self.W  * 0.5)
        dy = (pos.y() - orb_cy) / (self.H  * 0.5)
        self._orb_widget.look_at(dx, dy)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        pos = event.position().toPoint()
        _click_ripples.append([float(pos.x()), float(pos.y()), 0.0])
        super().mousePressEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.accept()
        os._exit(0)

    # ── Orb interactions ──────────────────────────────────────────────────
    def _orb_clicked(self) -> None:
        states = ["LISTENING", "THINKING", "SPEAKING", "PROCESSING"]
        idx = states.index(self._omini_state) if self._omini_state in states else 0
        nxt = states[(idx + 1) % len(states)]
        self.set_state(nxt)
        self.write_log(f"SYS: State → {nxt}")
        self._screen_shake = 5

    def _orb_right_clicked(self) -> None:
        # Show a context menu to choose theme or orb mode
        menu = QtWidgets.QMenu(self)
        theme_menu = menu.addMenu("Themes")
        for key, td in THEMES.items():
            act = QtGui.QAction(td["name"], self)
            act.triggered.connect(lambda _chk=False, k=key: self.set_theme(k))
            theme_menu.addAction(act)

        mode_menu = menu.addMenu("Orb Mode")
        for m in ("eye", "reactor", "orb"):
            act2 = QtGui.QAction(m.capitalize(), self)
            act2.triggered.connect(lambda _chk=False, mm=m: self.set_orb_mode(mm))
            mode_menu.addAction(act2)

        menu.addSeparator()
        act_cycle = QtGui.QAction("Cycle Theme", self)
        act_cycle.triggered.connect(self._cycle_theme)
        menu.addAction(act_cycle)

        # Execute at cursor position
        menu.exec(QtGui.QCursor.pos())

    def _on_orb_hover(self, hovered: bool) -> None:
        # Show a small tooltip near the orb with theme preview and hint
        if hovered:
            t = T()
            name = t.get('name', _current_theme.upper())
            mode = t.get('orb_mode', 'eye')
            txt = f"{name} — {mode.capitalize()}\nRight-click for themes/modes"
            self._orb_tooltip.setText(txt)
            # Position tooltip to the right of orb if space, else left
            ox = self._orb_widget.x()
            oy = self._orb_widget.y()
            ow = self._orb_widget.width()
            th = 60
            tx = ox + ow + 12
            ty = oy + max(0, (self._orb_widget.height() - th) // 2)
            if tx + 220 > self.W:
                tx = ox - 220 - 12
            self._orb_tooltip.setGeometry(tx, ty, 220, th)
            self._orb_tooltip.show()
        else:
            self._orb_tooltip.hide()

    # ── Selector callbacks ─────────────────────────────────────────────────
    def _on_persona_changed(self, index: int) -> None:
        if index < 0 or not self._persona_manager: return
        key  = str(self._persona_box.itemData(index) or "executive")
        prof = self._persona_manager.set_selected_key(key)
        self._selected_persona = prof.key
        self.write_log(f"SYS: Persona → {prof.title}")
        self.persona_changed.emit(prof.key)

    def _on_voice_changed(self, index: int) -> None:
        if index < 0 or not self._voice_manager: return
        key  = str(self._voice_box.itemData(index) or "en_us-danny-low")
        prof = self._voice_manager.set_selected_key(key)
        self._selected_voice = prof.key
        self.write_log(f"SYS: Voice → {prof.title}")
        self.voice_changed.emit(prof.key)

    def _on_live_voice_changed(self, index: int) -> None:
        if index < 0 or not self._live_voice_manager: return
        key  = str(self._live_voice_box.itemData(index) or "Charon")
        prof = self._live_voice_manager.set_selected_key(key)
        self._selected_live_voice = prof.key
        self.write_log(f"SYS: Live voice → {prof.title}")
        self.live_voice_changed.emit(prof.key)

    # ── Mute ───────────────────────────────────────────────────────────────
    def _toggle_mute(self) -> None:
        self.muted = not self.muted
        self._draw_mute_button()
        self._orb_widget.set_state(
            "MUTED" if self.muted else "LISTENING",
            speaking=False, muted=self.muted
        )
        self.set_state("MUTED" if self.muted else "LISTENING")
        self.write_log("SYS: Microphone muted." if self.muted else "SYS: Microphone active.")

    # ── Theme ──────────────────────────────────────────────────────────────
    def _cycle_theme(self) -> None:
        keys = list(THEMES.keys())
        idx  = keys.index(_current_theme) if _current_theme in keys else 0
        self.set_theme(keys[(idx + 1) % len(keys)])

    def set_theme(self, theme_name: str) -> None:
        global _current_theme
        if theme_name not in THEMES:
            return
        _current_theme = theme_name
        self._apply_bg_palette()
        self._style_log_frame()
        self._style_log_text()
        self._style_input()
        self._style_send_btn()
        self._draw_mute_button()
        for btn, key in self._theme_btns:
            self._style_theme_btn(btn, key)
        t2 = T()
        for w in self._selector_widgets:
            if isinstance(w, QtWidgets.QComboBox):
                w.setStyleSheet(f"""
                    QComboBox {{
                        color: {t2['text']}; background: {t2['dimmer']};
                        border: 1px solid {t2['dim']}; border-radius: 6px;
                        padding-left: 8px; font-family: 'Courier New', monospace; font-size: 8pt;
                    }}
                    QComboBox::drop-down {{ border: 0; width: 16px; }}
                    QComboBox QAbstractItemView {{
                        background: {t2['panel']}; color: {t2['text']};
                        selection-background-color: {t2['dim']};
                        border: 1px solid {t2['secondary']};
                    }}
                """)
            elif isinstance(w, QtWidgets.QLabel):
                w.setStyleSheet(f"""
                    QLabel {{
                        color: {t2['dim']}; font-family: 'Courier New', monospace;
                        font-size: 7pt; font-weight: 700; letter-spacing: 2px;
                        background: transparent;
                    }}
                """)
        if hasattr(self, '_motes'):
            del self._motes
        self.write_log(f"SYS: Theme switched → {theme_name.upper()}")
        self.update()

    def set_orb_mode(self, mode: str) -> None:
        # Mode should be one of: 'eye', 'reactor', 'orb'
        if mode not in ("eye", "reactor", "orb"):
            return
        # Apply temporarily to current theme so CentralOrbWidget will render accordingly
        tc = THEMES.get(_current_theme)
        if tc is not None:
            tc['orb_mode'] = mode
        if hasattr(self, '_orb_widget'):
            self._orb_widget.update()
        self.write_log(f"SYS: Orb mode set → {mode.upper()}")

    # ── Input ──────────────────────────────────────────────────────────────
    def _on_input_submit(self) -> None:
        text = self._input.text().strip()
        if not text: return
        self._input.clear()
        self.write_log(f"You: {text}")
        self._messages_sent += 1
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    # ── State machine ──────────────────────────────────────────────────────
    def set_state(self, state: str) -> None:
        self.state_requested.emit(state)

    def _set_state_impl(self, state: str) -> None:
        self._prev_state  = self._omini_state
        self._omini_state = state
        self.speaking     = (state == "SPEAKING")
        self._orb_widget.set_state(state, speaking=self.speaking, muted=(state == "MUTED"))
        self.update()

    # ── Log / typing ───────────────────────────────────────────────────────
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
        self.is_typing    = True
        self._typing_text = self.typing_queue.popleft()
        self._typing_idx  = 0
        t  = T()
        tl = self._typing_text.lower()
        if tl.startswith("you:"):
            self._typing_color = QtGui.QColor("#D0C0FF")
        elif tl.startswith("omini:") or tl.startswith("ai:"):
            self._typing_color = QtGui.QColor(t["primary"])
        elif "error" in tl or "failed" in tl:
            self._typing_color = QtGui.QColor(t["red"])
        else:
            self._typing_color = QtGui.QColor(t["gold"])
        self._type_char()

    def _type_char(self) -> None:
        if self._typing_idx < len(self._typing_text):
            cur = self.log_text.textCursor()
            cur.movePosition(QtGui.QTextCursor.MoveOperation.End)
            self.log_text.setTextCursor(cur)
            self.log_text.setTextColor(self._typing_color)
            self.log_text.insertPlainText(self._typing_text[self._typing_idx])
            self.log_text.ensureCursorVisible()
            self._typing_idx += 1
            QtCore.QTimer.singleShot(7, self._type_char)
            return
        self.log_text.insertPlainText("\n")
        self.log_text.ensureCursorVisible()
        QtCore.QTimer.singleShot(20, self._start_typing)

    # ── API key setup ──────────────────────────────────────────────────────
    def _api_keys_exist(self) -> bool:
        if not API_FILE.exists(): return False
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
        if s == "darwin":  return "mac"
        if s == "windows": return "windows"
        return "linux"

    def _show_setup_ui(self) -> None:
        t = T()
        detected = self._detect_os()
        dlg = QtWidgets.QDialog(self)
        dlg.setModal(True)
        dlg.setWindowTitle("OMINI — First Boot")
        dlg.setStyleSheet(f"""
            QDialog {{ background: {t['bg']}; }}
            QLabel   {{ font-family: 'Courier New'; }}
            QLineEdit {{
                background: {t['dimmer']}; color: {t['text']};
                border: 1px solid {t['dim']}; border-radius: 8px;
                padding: 10px; font-family: 'Courier New'; font-size: 10pt;
            }}
            QLineEdit:focus {{ border: 1px solid {t['secondary']}; }}
        """)
        layout = QtWidgets.QVBoxLayout(dlg)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        hdr = QtWidgets.QLabel("SYSTEM INITIALISATION")
        hdr.setStyleSheet(f"color:{t['primary']}; font-size:13pt; font-weight:700;")
        layout.addWidget(hdr, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        sub = QtWidgets.QLabel("Configure your OMINI neural core before awakening.")
        sub.setStyleSheet(f"color:{t['secondary']}; font-size:9pt;")
        layout.addWidget(sub, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        for _ in range(2):
            sep = QtWidgets.QFrame()
            sep.setFrameShape(QtWidgets.QFrame.Shape.HLine)
            sep.setStyleSheet(f"background:{t['dim']}; min-height:1px; max-height:1px;")
            layout.addWidget(sep)

        cap = QtWidgets.QLabel("GEMINI API KEY")
        cap.setStyleSheet(f"color:{t['dim']}; font-size:9pt; font-weight:700;")
        layout.addWidget(cap)
        gemini_entry = QtWidgets.QLineEdit()
        gemini_entry.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        gemini_entry.setMinimumHeight(42)
        layout.addWidget(gemini_entry)

        os_lbl = QtWidgets.QLabel("OPERATING SYSTEM")
        os_lbl.setStyleSheet(f"color:{t['dim']}; font-size:9pt; font-weight:700;")
        layout.addWidget(os_lbl)

        det_map = {"windows": "Windows", "mac": "macOS", "linux": "Linux"}
        auto_lbl = QtWidgets.QLabel(f"Auto-detected: {det_map.get(detected, detected)}")
        auto_lbl.setStyleSheet(f"color:{t['gold']}; font-size:8pt;")
        layout.addWidget(auto_lbl, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        os_row = QtWidgets.QHBoxLayout()
        os_row.setSpacing(8)
        layout.addLayout(os_row)

        group = QtWidgets.QButtonGroup(dlg)
        group.setExclusive(True)
        os_buttons: dict[str, QtWidgets.QPushButton] = {}
        selected_os = {"key": detected}

        def apply_os_style(active: str) -> None:
            for k, b in os_buttons.items():
                if k == active:
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background:{t['dim']}; color:{t['primary']};
                            border:1px solid {t['secondary']}; padding:8px;
                            font-family:'Courier New'; font-size:10pt; font-weight:700;
                            border-radius:7px;
                        }}
                    """)
                    b.setChecked(True)
                else:
                    b.setStyleSheet(f"""
                        QPushButton {{
                            background:{t['dimmer']}; color:{t['dim']};
                            border:1px solid {t['dim']}; padding:8px;
                            font-family:'Courier New'; font-size:10pt; font-weight:700;
                            border-radius:7px;
                        }}
                        QPushButton:hover {{ color:{t['text']}; }}
                    """)
                    b.setChecked(False)

        for key, label in [("windows", "WINDOWS"), ("mac", "macOS"), ("linux", "LINUX")]:
            b = QtWidgets.QPushButton(label)
            b.setCheckable(True)
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            group.addButton(b)
            os_row.addWidget(b)
            os_buttons[key] = b
            b.clicked.connect(lambda _=False, k=key: (
                selected_os.__setitem__("key", k),
                apply_os_style(k)
            ))

        apply_os_style(detected)

        save_btn = QtWidgets.QPushButton("◈  BOOT NEURAL CORE")
        save_btn.setMinimumHeight(46)
        save_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {t['indigo']}, stop:1 {t['accent2']});
                color:#F0E6FF; border:none; border-radius:9px;
                font-family:'Courier New'; font-size:10pt; font-weight:700;
                padding:12px; letter-spacing:2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {t['secondary']}, stop:1 {t['primary']});
            }}
        """)
        layout.addWidget(save_btn)

        def on_save() -> None:
            gemini = gemini_entry.text().strip()
            if not gemini:
                gemini_entry.setStyleSheet(f"""
                    QLineEdit {{
                        background:{t['dimmer']}; color:{t['text']};
                        border:1px solid {t['red']}; border-radius:8px; padding:10px;
                    }}
                """)
                return
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(API_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "gemini_api_key": gemini,
                    "os_system": selected_os["key"]
                }, f, indent=4)
            self._api_key_ready = True
            self.set_state("LISTENING")
            self.write_log(f"SYS: Neural core online. OS → {selected_os['key'].upper()}.")
            dlg.accept()

        save_btn.clicked.connect(on_save)
        dlg.resize(540, 420)
        dlg.exec()

    # ── Helpers ────────────────────────────────────────────────────────────
    def _get_uptime(self) -> str:
        e = int(time.time() - self._start_time)
        return f"{e // 3600:02d}:{(e % 3600) // 60:02d}:{e % 60:02d}"

    # ── Public API ─────────────────────────────────────────────────────────
    def start_speaking(self) -> None:
        self.set_state("SPEAKING")

    def stop_speaking(self) -> None:
        if not self.muted:
            self.set_state("LISTENING")

    def get_theme(self) -> str:           return _current_theme
    def get_persona(self) -> str:         return self._selected_persona
    def get_voice(self) -> str:           return self._selected_voice
    def get_live_voice(self) -> str:      return self._selected_live_voice

    def set_persona(self, key: str) -> None:
        if not self._persona_manager: return
        prof = self._persona_manager.set_selected_key(key)
        self._selected_persona = prof.key
        if hasattr(self, "_persona_box"):
            idx = self._persona_box.findData(prof.key)
            if idx >= 0:
                self._persona_box.blockSignals(True)
                self._persona_box.setCurrentIndex(idx)
                self._persona_box.blockSignals(False)

    def set_voice(self, key: str) -> None:
        if not self._voice_manager: return
        prof = self._voice_manager.set_selected_key(key)
        self._selected_voice = prof.key
        if hasattr(self, "_voice_box"):
            idx = self._voice_box.findData(prof.key)
            if idx >= 0:
                self._voice_box.blockSignals(True)
                self._voice_box.setCurrentIndex(idx)
                self._voice_box.blockSignals(False)

    def set_live_voice(self, key: str) -> None:
        if not self._live_voice_manager: return
        prof = self._live_voice_manager.set_selected_key(key)
        self._selected_live_voice = prof.key
        if hasattr(self, "_live_voice_box"):
            idx = self._live_voice_box.findData(prof.key)
            if idx >= 0:
                self._live_voice_box.blockSignals(True)
                self._live_voice_box.setCurrentIndex(idx)
                self._live_voice_box.blockSignals(False)

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


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE DEMO
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("OMINI v3")

    ui = OminiUI(face_path="", size=(1040, 840))
    ui.show()

    def _demo() -> None:
        time.sleep(1.4)
        ui.state_requested.emit("LISTENING")
        ui.log_requested.emit("SYS: O.M.I.N.I v3 neural core awakened.")
        ui.log_requested.emit("SYS: Three themes ready — AMETHYST · HOGWARTS · AVENGERS")
        ui.log_requested.emit("SYS: Left-click orb to cycle states · Right-click to cycle themes.")
        ui.log_requested.emit("SYS: F4=mute · F5=theme · F11=fullscreen · Mouse=gaze tracking.")
        ui.log_requested.emit("SYS: Scroll wheel on orb to adjust animation intensity.")
        time.sleep(3.2)
        ui.log_requested.emit("OMINI: All neural pathways nominal. How may I assist?")
        time.sleep(2.8)
        ui.state_requested.emit("THINKING")
        time.sleep(2.0)
        ui.state_requested.emit("LISTENING")

    threading.Thread(target=_demo, daemon=True).start()

    def handle_cmd(text: str) -> None:
        time.sleep(0.35)
        ui.state_requested.emit("THINKING")
        time.sleep(1.1)
        ui.state_requested.emit("SPEAKING")
        ui.log_requested.emit(f"OMINI: Processing command — '{text}'")
        time.sleep(2.2)
        ui.state_requested.emit("LISTENING")

    ui.on_text_command = handle_cmd
    sys.exit(app.exec())