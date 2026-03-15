"""Forgot-password two-step wizard window."""

import threading
import customtkinter as ctk
from services import api_client


class ForgotPasswordWindow(ctk.CTkToplevel):
    """
    Two-step forgot-password wizard.

    Step 1 — Request: user enters their email address.
              The backend sends a one-time token to that address.

    Step 2 — Confirm: user pastes the token and chooses a new password.
              On success the window closes and the caller can redirect to login.
    """

    def __init__(self, parent, on_success=None):
        """
        Parameters
        ----------
        parent : tk widget
            Parent window (typically LoginWindow or the root).
        on_success : callable, optional
            Invoked with no arguments once the password has been reset.
        """
        super().__init__(parent)

        self.on_success = on_success

        self.title("OmniAssist – Forgot Password")
        self.geometry("460x540")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (460 // 2)
        y = (self.winfo_screenheight() // 2) - (540 // 2)
        self.geometry(f"460x540+{x}+{y}")

        # Root container – rebuilt when switching steps
        self._root_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._root_frame.pack(fill="both", expand=True, padx=24, pady=24)

        self._build_step1()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clear_root(self):
        for w in self._root_frame.winfo_children():
            w.destroy()

    def _header(self, container, title: str, subtitle: str):
        ctk.CTkLabel(
            container,
            text="🔑 Password Recovery",
            font=("Segoe UI", 26, "bold"),
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            container,
            text=title,
            font=("Segoe UI", 13, "bold"),
            text_color="#00ccff",
        ).pack(pady=(0, 2))
        ctk.CTkLabel(
            container,
            text=subtitle,
            font=("Segoe UI", 10),
            text_color="gray70",
            wraplength=390,
            justify="center",
        ).pack(pady=(0, 20))

    def _status_label(self, container) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(
            container,
            text="",
            font=("Segoe UI", 10),
            text_color="#ff6b7d",
            wraplength=390,
            justify="center",
        )
        lbl.pack(pady=(4, 0))
        return lbl

    # ------------------------------------------------------------------
    # Step 1 – Email request
    # ------------------------------------------------------------------

    def _build_step1(self):
        self._clear_root()
        f = self._root_frame

        self._header(
            f,
            "Step 1 of 2 – Request Reset Email",
            "Enter the email address linked to your account.\n"
            "We will send you a one-time reset token.",
        )

        box = ctk.CTkFrame(f, fg_color="gray20", corner_radius=12)
        box.pack(fill="x")

        ctk.CTkLabel(box, text="Email address", font=("Segoe UI", 11, "bold"),
                     text_color="gray95").pack(anchor="w", padx=18, pady=(18, 6))

        self._email_entry = ctk.CTkEntry(
            box,
            placeholder_text="your@email.com",
            height=42,
            font=("Segoe UI", 11),
            corner_radius=8,
        )
        self._email_entry.pack(fill="x", padx=18, pady=(0, 6))

        self._step1_status = self._status_label(box)

        self._step1_btn = ctk.CTkButton(
            box,
            text="📧 Send Reset Email",
            font=("Segoe UI", 13, "bold"),
            height=44,
            corner_radius=8,
            fg_color="#00ccff",
            text_color="black",
            hover_color="#00aadd",
            command=self._handle_request,
        )
        self._step1_btn.pack(fill="x", padx=18, pady=(10, 18))

        ctk.CTkButton(
            f,
            text="← Back to Login",
            font=("Segoe UI", 11),
            height=36,
            corner_radius=8,
            fg_color="transparent",
            text_color="gray70",
            hover_color="gray25",
            command=self.destroy,
        ).pack(pady=(14, 0))

        self._email_entry.bind("<Return>", lambda e: self._handle_request())

    def _handle_request(self):
        email = self._email_entry.get().strip()
        if not email:
            self._step1_status.configure(text="❌ Please enter your email address.", text_color="#ff6b7d")
            return
        if "@" not in email:
            self._step1_status.configure(text="❌ Please enter a valid email address.", text_color="#ff6b7d")
            return

        self._step1_btn.configure(state="disabled", text="⏳ Sending…")
        self._step1_status.configure(text="", text_color="#ff6b7d")

        def _worker():
            success, message = api_client.request_password_reset(email)
            self.after(0, lambda: self._on_request_result(success, message))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_request_result(self, success: bool, message: str):
        if success:
            self._build_step2(message)
        else:
            self._step1_status.configure(text=f"❌ {message}", text_color="#ff6b7d")
            self._step1_btn.configure(state="normal", text="📧 Send Reset Email")

    # ------------------------------------------------------------------
    # Step 2 – Token + new password
    # ------------------------------------------------------------------

    def _build_step2(self, info_message: str):
        self._clear_root()
        # Resize to accommodate more fields
        self.geometry("460x620")
        self.update_idletasks()

        f = self._root_frame

        self._header(
            f,
            "Step 2 of 2 – Set New Password",
            info_message,
        )

        box = ctk.CTkFrame(f, fg_color="gray20", corner_radius=12)
        box.pack(fill="x")

        # Token field
        ctk.CTkLabel(box, text="Reset token (from email)", font=("Segoe UI", 11, "bold"),
                     text_color="gray95").pack(anchor="w", padx=18, pady=(18, 6))

        self._token_entry = ctk.CTkEntry(
            box,
            placeholder_text="Paste the token you received",
            height=42,
            font=("Segoe UI", 11),
            corner_radius=8,
        )
        self._token_entry.pack(fill="x", padx=18, pady=(0, 14))

        # New password
        ctk.CTkLabel(box, text="New password", font=("Segoe UI", 11, "bold"),
                     text_color="gray95").pack(anchor="w", padx=18, pady=(0, 6))

        pwd_row = ctk.CTkFrame(box, fg_color="transparent")
        pwd_row.pack(fill="x", padx=18, pady=(0, 14))

        self._new_pwd_entry = ctk.CTkEntry(
            pwd_row,
            placeholder_text="Min 8 chars, upper + lower + digit",
            show="●",
            height=42,
            font=("Segoe UI", 11),
            corner_radius=8,
        )
        self._new_pwd_entry.pack(side="left", fill="both", expand=True)

        self._show_pwd = False
        self._eye_btn = ctk.CTkButton(
            pwd_row,
            text="👁️",
            width=42,
            height=42,
            font=("Segoe UI", 14),
            fg_color="gray30",
            hover_color="gray40",
            corner_radius=8,
            command=self._toggle_password,
        )
        self._eye_btn.pack(side="left", padx=(8, 0))

        # Confirm password
        ctk.CTkLabel(box, text="Confirm new password", font=("Segoe UI", 11, "bold"),
                     text_color="gray95").pack(anchor="w", padx=18, pady=(0, 6))

        self._confirm_pwd_entry = ctk.CTkEntry(
            box,
            placeholder_text="Repeat new password",
            show="●",
            height=42,
            font=("Segoe UI", 11),
            corner_radius=8,
        )
        self._confirm_pwd_entry.pack(fill="x", padx=18, pady=(0, 6))

        self._step2_status = self._status_label(box)

        self._step2_btn = ctk.CTkButton(
            box,
            text="🔒 Reset Password",
            font=("Segoe UI", 13, "bold"),
            height=44,
            corner_radius=8,
            fg_color="#00ff99",
            text_color="black",
            hover_color="#00dd77",
            command=self._handle_confirm,
        )
        self._step2_btn.pack(fill="x", padx=18, pady=(10, 18))

        ctk.CTkButton(
            f,
            text="← Request a new token instead",
            font=("Segoe UI", 11),
            height=36,
            corner_radius=8,
            fg_color="transparent",
            text_color="gray70",
            hover_color="gray25",
            command=self._build_step1,
        ).pack(pady=(14, 0))

        self._confirm_pwd_entry.bind("<Return>", lambda e: self._handle_confirm())

    def _toggle_password(self):
        self._show_pwd = not self._show_pwd
        char = "" if self._show_pwd else "●"
        icon = "🙈" if self._show_pwd else "👁️"
        self._new_pwd_entry.configure(show=char)
        self._confirm_pwd_entry.configure(show=char)
        self._eye_btn.configure(text=icon)

    def _handle_confirm(self):
        token = self._token_entry.get().strip()
        new_pwd = self._new_pwd_entry.get()
        confirm_pwd = self._confirm_pwd_entry.get()

        if not token:
            self._step2_status.configure(text="❌ Please paste the reset token from your email.", text_color="#ff6b7d")
            return
        if not new_pwd:
            self._step2_status.configure(text="❌ Please enter a new password.", text_color="#ff6b7d")
            return
        if new_pwd != confirm_pwd:
            self._step2_status.configure(text="❌ Passwords do not match.", text_color="#ff6b7d")
            return
        if len(new_pwd) < 8:
            self._step2_status.configure(text="❌ Password must be at least 8 characters.", text_color="#ff6b7d")
            return

        self._step2_btn.configure(state="disabled", text="⏳ Resetting…")
        self._step2_status.configure(text="", text_color="#ff6b7d")

        def _worker():
            success, message = api_client.confirm_password_reset(token, new_pwd)
            self.after(0, lambda: self._on_confirm_result(success, message))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_confirm_result(self, success: bool, message: str):
        if success:
            self._step2_status.configure(
                text=f"✅ {message}\n\nYou can now log in with your new password.",
                text_color="#00ff99",
            )
            self._step2_btn.configure(text="✅ Done", state="disabled")
            if self.on_success:
                self.after(2500, self.on_success)
            self.after(2500, self.destroy)
        else:
            self._step2_status.configure(text=f"❌ {message}", text_color="#ff6b7d")
            self._step2_btn.configure(state="normal", text="🔒 Reset Password")
