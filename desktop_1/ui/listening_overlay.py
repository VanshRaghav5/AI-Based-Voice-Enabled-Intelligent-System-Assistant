import customtkinter as ctk
from .siri_orb import SiriOrb


class AssistantState:
    """Enumeration of assistant states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"


class ListeningOverlay(ctk.CTkToplevel):
    """
    Fullscreen Siri-style overlay with a glowing orb, live transcript,
    and smooth fade-in / fade-out transitions.

    States
    ------
    IDLE        – overlay hidden
    LISTENING   – overlay visible, orb reacts to amplitude
    PROCESSING  – overlay visible, orb slow-pulses, text = "Processing…"
    RESPONDING  – fade-out, result goes to chat
    """

    FADE_STEP_MS = 20          # milliseconds per fade step
    FADE_INCREMENTS = 15       # number of steps for a full fade

    def __init__(self, master):
        self._assistant_state = AssistantState.IDLE

        super().__init__(master)

        # ── window chrome ───────────────────────────────────────
        self.title("OmniAssist AI")
        self.configure(fg_color="black")
        self.attributes("-alpha", 0.0)
        self.attributes("-topmost", True)
        self.overrideredirect(True)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        # ── background ──────────────────────────────────────────
        self.bg_frame = ctk.CTkFrame(self, fg_color="#050510", corner_radius=0)
        self.bg_frame.pack(fill="both", expand=True)

        # ── centred content ─────────────────────────────────────
        self.content = ctk.CTkFrame(self.bg_frame, fg_color="transparent")
        self.content.place(relx=0.5, rely=0.45, anchor="center")

        # Status label (top of content)
        self.status_label = ctk.CTkLabel(
            self.content,
            text="Listening…",
            font=("Inter", 34, "bold"),
            text_color="#FFFFFF",
        )
        self.status_label.pack(pady=(0, 50))

        # Siri orb
        self.orb = SiriOrb(self.content, base_size=200, bg="#050510")
        self.orb.pack()

        # ── transcript (bottom) ─────────────────────────────────
        self.transcript_label = ctk.CTkLabel(
            self.bg_frame,
            text="",
            font=("Inter", 22, "italic"),
            text_color="#AAAAAA",
            wraplength=int(screen_w * 0.75),
        )
        self.transcript_label.place(relx=0.5, rely=0.82, anchor="center")

        # ── close button (top-right) ────────────────────────────
        self.close_btn = ctk.CTkButton(
            self.bg_frame,
            text="✕  Close",
            width=110,
            height=36,
            corner_radius=18,
            fg_color="#222222",
            hover_color="#444444",
            font=("Inter", 12, "bold"),
            text_color="#AAAAAA",
            command=self.hide,
        )
        self.close_btn.place(relx=0.95, rely=0.04, anchor="ne")

        # ── internal fade tracking ──────────────────────────────
        self._fade_after_id = None
        self._target_alpha = 0.0
        self._fade_callback = None

        self.withdraw()

    # ── state property ──────────────────────────────────────────

    @property
    def assistant_state(self) -> str:
        return self._assistant_state

    # ── public API ──────────────────────────────────────────────

    def show(self):
        """Transition into LISTENING state with a fade-in."""
        self._assistant_state = AssistantState.LISTENING

        self.transcript_label.configure(text="")
        self.status_label.configure(text="Listening…", text_color="#FFFFFF")

        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        self._fade_to(0.97)
        # safety re-lift on Windows
        self.after(120, self.lift)

    def hide(self):
        """Fade out and withdraw (→ IDLE)."""
        self._assistant_state = AssistantState.IDLE
        self._fade_to(0.0, on_done=self._withdraw_after_fade)

    def set_processing(self):
        """Switch overlay to PROCESSING state (slow orb pulse, status text)."""
        self._assistant_state = AssistantState.PROCESSING
        self.status_label.configure(text="Processing…", text_color="#A78BFA")
        self.transcript_label.configure(text="")
        # Reset orb to idle so it does the breathing animation
        if hasattr(self, "orb"):
            self.orb.set_amplitude(0.0)

    def set_responding(self):
        """Begin RESPONDING → fade out overlay."""
        self._assistant_state = AssistantState.RESPONDING
        self.hide()

    def update_transcript(self, text: str):
        """Update the live speech transcript."""
        self.transcript_label.configure(text=f'"{text}"')

    def set_amplitude(self, amplitude: float):
        """Forward amplitude to the orb (only reacts in LISTENING state)."""
        if self._assistant_state == AssistantState.LISTENING and hasattr(self, "orb"):
            self.orb.set_amplitude(amplitude)

    # ── fade helpers ────────────────────────────────────────────

    def _fade_to(self, target: float, on_done=None):
        """Smoothly animate window alpha to *target* (0.0 – 1.0)."""
        if self._fade_after_id is not None:
            self.after_cancel(self._fade_after_id)
            self._fade_after_id = None

        self._target_alpha = target
        self._fade_callback = on_done
        self._fade_step()

    def _fade_step(self):
        try:
            current = float(self.attributes("-alpha"))
        except Exception:
            return

        diff = self._target_alpha - current
        if abs(diff) < 0.02:
            self.attributes("-alpha", self._target_alpha)
            if self._fade_callback:
                self._fade_callback()
                self._fade_callback = None
            return

        step = diff / max(self.FADE_INCREMENTS, 3)
        new_alpha = current + step
        new_alpha = max(0.0, min(1.0, new_alpha))
        self.attributes("-alpha", new_alpha)
        self._fade_after_id = self.after(self.FADE_STEP_MS, self._fade_step)

    def _withdraw_after_fade(self):
        """Called once fade-out completes."""
        self.withdraw()
