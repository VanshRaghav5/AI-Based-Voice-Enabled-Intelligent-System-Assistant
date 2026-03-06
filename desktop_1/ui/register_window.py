"""Registration window for new user signup."""

import customtkinter as ctk
from typing import Callable, Optional
import re


class RegisterWindow(ctk.CTkToplevel):
    """Registration window for new user signup."""
    
    def __init__(self, parent, on_register_success: Callable, on_back: Optional[Callable] = None):
        """
        Initialize registration window.
        
        Args:
            parent: Parent window
            on_register_success: Callback when registration succeeds
            on_back: Callback to go back to login
        """
        super().__init__(parent)
        
        self.on_register_success = on_register_success
        self.on_back = on_back
        
        # Window configuration
        self.title("OmniAssist Registration")
        self.geometry("450x600")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"450x600+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build registration UI components."""
        # Main container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Logo/Title
        title = ctk.CTkLabel(
            container,
            text="🎙️ OmniAssist",
            font=("Segoe UI", 28, "bold")
        )
        title.pack(pady=(0, 5))
        
        subtitle = ctk.CTkLabel(
            container,
            text="Create New Account",
            font=("Segoe UI", 14),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 25))
        
        # Registration form
        form_frame = ctk.CTkFrame(container)
        form_frame.pack(fill="both", expand=True)
        
        # Username
        ctk.CTkLabel(
            form_frame,
            text="Username",
            font=("Segoe UI", 11),
            anchor="w"
        ).pack(fill="x", padx=15, pady=(15, 5))
        
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="3-50 characters, letters/numbers/_",
            height=38,
            font=("Segoe UI", 11)
        )
        self.username_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Email
        ctk.CTkLabel(
            form_frame,
            text="Email Address",
            font=("Segoe UI", 11),
            anchor="w"
        ).pack(fill="x", padx=15, pady=(0, 5))
        
        self.email_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="your@email.com",
            height=38,
            font=("Segoe UI", 11)
        )
        self.email_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Password
        ctk.CTkLabel(
            form_frame,
            text="Password",
            font=("Segoe UI", 11),
            anchor="w"
        ).pack(fill="x", padx=15, pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Min 6 chars, 1 uppercase, 1 number",
            show="●",
            height=38,
            font=("Segoe UI", 11)
        )
        self.password_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Confirm Password
        ctk.CTkLabel(
            form_frame,
            text="Confirm Password",
            font=("Segoe UI", 11),
            anchor="w"
        ).pack(fill="x", padx=15, pady=(0, 5))
        
        self.confirm_password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Re-enter your password",
            show="●",
            height=38,
            font=("Segoe UI", 11)
        )
        self.confirm_password_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Show password checkbox
        self.show_password_var = ctk.BooleanVar(value=False)
        show_password_cb = ctk.CTkCheckBox(
            form_frame,
            text="Show passwords",
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            font=("Segoe UI", 10)
        )
        show_password_cb.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Error message label
        self.error_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=("Segoe UI", 10),
            text_color="red"
        )
        self.error_label.pack(fill="x", padx=15, pady=(0, 10))
        
        # Info box
        info_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        info_text = (
            "ℹ️ Password must contain:\n"
            "  • At least 1 uppercase letter\n"
            "  • At least 1 lowercase letter\n"
            "  • At least 1 number"
        )
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Segoe UI", 9),
            text_color="gray",
            justify="left"
        ).pack(anchor="w")
        
        # Register button
        self.register_button = ctk.CTkButton(
            form_frame,
            text="Register",
            height=42,
            font=("Segoe UI", 13, "bold"),
            command=self._handle_register
        )
        self.register_button.pack(fill="x", padx=15, pady=(10, 10))
        
        # Back to login link
        if self.on_back:
            back_btn = ctk.CTkButton(
                form_frame,
                text="Back to Login",
                height=38,
                font=("Segoe UI", 12),
                fg_color="gray30",
                hover_color="gray40",
                command=self._handle_back
            )
            back_btn.pack(fill="x", padx=15)
        
        # Bind Enter key to register
        self.confirm_password_entry.bind("<Return>", lambda e: self._handle_register())
    
    def _toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.show_password_var.get():
            self.password_entry.configure(show="")
            self.confirm_password_entry.configure(show="")
        else:
            self.password_entry.configure(show="●")
            self.confirm_password_entry.configure(show="●")
    
    def _handle_register(self):
        """Handle register button click."""
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        # Validation
        if not username:
            self.show_error("Please enter a username")
            return
        
        if not email:
            self.show_error("Please enter your email")
            return
        
        if not password:
            self.show_error("Please enter a password")
            return
        
        if password != confirm_password:
            self.show_error("Passwords do not match")
            return
        
        # Disable button during registration
        self.register_button.configure(state="disabled", text="Registering...")
        self.error_label.configure(text="")
        
        # Call register callback
        try:
            self.on_register_success(username, email, password, self._on_register_result)
        except Exception as e:
            self._on_register_result(False, str(e))
    
    def _on_register_result(self, success: bool, message: str):
        """
        Handle registration result.
        
        Args:
            success: Whether registration succeeded
            message: Success or error message
        """
        if success:
            # Show success message and close
            self.show_error(message, is_error=False)
            self.after(1500, self.destroy)
        else:
            # Show error and re-enable button
            self.show_error(message)
            self.register_button.configure(state="normal", text="Register")
    
    def _handle_back(self):
        """Handle back button click."""
        if self.on_back:
            self.destroy()
            self.on_back()
    
    def show_error(self, message: str, is_error: bool = True):
        """Show error or success message."""
        if is_error:
            self.error_label.configure(text=message, text_color="red")
        else:
            self.error_label.configure(text=f"✅ {message}", text_color="green")
