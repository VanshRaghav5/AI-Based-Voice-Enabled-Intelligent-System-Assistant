import customtkinter as ctk
import math
import time


class SiriOrb(ctk.CTkCanvas):
    """
    Siri-style glowing orb visualizer.

    Draws a circular orb that expands/contracts based on microphone
    amplitude, with smooth interpolation and layered glow rings.
    """

    # Gradient palette: outer-most glow → inner core
    GLOW_LAYERS = [
        {"offset": 60, "fill": "#0a1a3a", "outline": "#0d2257"},
        {"offset": 45, "fill": "#0f2b5c", "outline": "#143a7a"},
        {"offset": 30, "fill": "#173f8a", "outline": "#1b4ea6"},
        {"offset": 18, "fill": "#1d5cc0", "outline": "#2468d4"},
        {"offset": 8,  "fill": "#2874e0", "outline": "#3384f0"},
    ]

    def __init__(self, master, base_size=150, **kwargs):
        """
        Args:
            master: Parent widget.
            base_size: Resting diameter of the orb (pixels).
        """
        canvas_dim = int(base_size * 3)
        kwargs.setdefault("bg", "#000000")
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("width", canvas_dim)
        kwargs.setdefault("height", canvas_dim)

        super().__init__(master, **kwargs)

        self.base_size = base_size
        self.current_size = float(base_size)
        self.target_size = float(base_size)
        self._canvas_dim = canvas_dim

        # Core gradient colours
        self.core_color = "#3B82F6"
        self.core_highlight = "#60A5FA"

        self._anim_running = True
        self._draw_orb()
        self._animate_smoothly()

    # ── public API ──────────────────────────────────────────────

    def set_amplitude(self, amplitude: float):
        """Set the target amplitude (0.0 – 1.0) that the orb expands to."""
        expansion = self.base_size * max(0.0, min(1.0, amplitude)) * 1.5
        self.target_size = self.base_size + expansion

    def destroy(self):
        self._anim_running = False
        super().destroy()

    # ── drawing ─────────────────────────────────────────────────

    def _draw_orb(self):
        """Redraw the orb with layered glow rings + solid core."""
        self.delete("all")

        cx = self.winfo_width() / 2
        cy = self.winfo_height() / 2
        if cx <= 1:
            cx = cy = self._canvas_dim / 2

        radius = max(5, self.current_size / 2)

        # Outer glow layers (large → small)
        for layer in self.GLOW_LAYERS:
            r = radius + layer["offset"]
            self.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=layer["fill"],
                outline=layer["outline"],
                width=2,
                tags="orb",
            )

        # Bright core
        self.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            fill=self.core_color,
            outline=self.core_color,
            tags="orb",
        )

        # Small inner highlight for depth
        hr = radius * 0.45
        self.create_oval(
            cx - hr, cy - hr - radius * 0.12,
            cx + hr, cy + hr - radius * 0.12,
            fill=self.core_highlight,
            outline=self.core_highlight,
            tags="orb",
        )

    # ── animation loop ──────────────────────────────────────────

    def _animate_smoothly(self):
        """~33 FPS lerp loop + idle breathing pulse."""
        if not self._anim_running:
            return

        lerp_factor = 0.18
        diff = self.target_size - self.current_size

        if abs(diff) > 0.5:
            self.current_size += diff * lerp_factor
        else:
            # Subtle breathing when idle
            pulse = math.sin(time.time() * 3.0) * 4.0
            self.current_size = self.base_size + pulse

        self._draw_orb()
        self.after(30, self._animate_smoothly)
