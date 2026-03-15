"""Login window for authentication."""

import customtkinter as ctk
from typing import Callable, Optional
from ui.forgot_password_window import ForgotPasswordWindow


class LoginWindow(ctk.CTkToplevel):
    """Login window with prominent registration option."""
    
    def __init__(self, parent, on_login_success: Callable, on_register: Optional[Callable] = None):
        """
        Initialize login window.
        
        Args:
            parent: Parent window
            on_login_success: Callback when login succeeds (username, password, callback)
            on_register: Optional callback to show registration window
        """
        super().__init__(parent)
        
        self.on_login_success = on_login_success
        self.on_register = on_register
        
        # Window configuration
        self.title("OmniAssist - Login & Registration")
        self.geometry("480x750")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (480 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"480x750+{x}+{y}")
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build login UI components."""
        # Main scrollable container
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        container = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=25)
        
        # ===== HEADER =====
        title = ctk.CTkLabel(
            container,
            text="🎙️ OmniAssist",
            font=("Segoe UI", 32, "bold")
        )
        title.pack(pady=(0, 3))
        
        subtitle = ctk.CTkLabel(
            container,
            text="Voice-Enabled Intelligent Assistant",
            font=("Segoe UI", 11),
            text_color="gray70"
        )
        subtitle.pack(pady=(0, 25))
        
        # ===== LOGIN SECTION =====
        login_header = ctk.CTkLabel(
            container,
            text="👤 LOGIN",
            font=("Segoe UI", 14, "bold"),
            text_color="#00ccff"
        )
        login_header.pack(anchor="w", padx=5, pady=(0, 12))
        
        # Login form box
        form_frame = ctk.CTkFrame(container, fg_color="gray20", corner_radius=12)
        form_frame.pack(fill="x", padx=0, pady=(0, 5))
        
        # Username field
        ctk.CTkLabel(
            form_frame,
            text="Username",
            font=("Segoe UI", 11, "bold"),
            text_color="gray95"
        ).pack(anchor="w", padx=18, pady=(18, 6))
        
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter your username",
            height=42,
            font=("Segoe UI", 11),
            corner_radius=8
        )
        self.username_entry.pack(fill="x", padx=18, pady=(0, 14))
        
        # Password field
        ctk.CTkLabel(
            form_frame,
            text="Password",
            font=("Segoe UI", 11, "bold"),
            text_color="gray95"
        ).pack(anchor="w", padx=18, pady=(0, 6))
        
        password_container = ctk.CTkFrame(form_frame, fg_color="transparent")
        password_container.pack(fill="x", padx=18, pady=(0, 12))
        
        self.password_entry = ctk.CTkEntry(
            password_container,
            placeholder_text="Enter your password",
            show="●",
            height=42,
            font=("Segoe UI", 11),
            corner_radius=8
        )
        self.password_entry.pack(side="left", fill="both", expand=True)
        
        self.show_pwd_btn = ctk.CTkButton(
            password_container,
            text="👁️",
            width=42,
            height=42,
            font=("Segoe UI", 14),
            command=self._toggle_password,
            corner_radius=8,
            fg_color="gray30",
            hover_color="gray40"
        )
        self.show_pwd_btn.pack(side="left", padx=(8, 0))
        
        self.show_password = False
        
        # Error label
        self.error_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=("Segoe UI", 10),
            text_color="#ff6b7d",
            wraplength=400
        )
        self.error_label.pack(padx=18, pady=(0, 12))
        
        # Login button
        self.login_button = ctk.CTkButton(
            form_frame,
            text="🔓 Login",
            font=("Segoe UI", 13, "bold"),
            height=44,
            corner_radius=8,
            fg_color="#00ccff",
            text_color="black",
            hover_color="#00aadd",
            command=self._handle_login
        )
        self.login_button.pack(fill="x", padx=18, pady=(0, 8))

        # Forgot password link
        forgot_btn = ctk.CTkButton(
            form_frame,
            text="🔑 Forgot password?",
            font=("Segoe UI", 10),
            height=28,
            corner_radius=6,
            fg_color="transparent",
            text_color="gray70",
            hover_color="gray25",
            command=self._handle_forgot_password
        )
        forgot_btn.pack(fill="x", padx=18, pady=(0, 12))

        # Admin info box
        admin_frame = ctk.CTkFrame(form_frame, fg_color="gray25", corner_radius=8)
        admin_frame.pack(fill="x", padx=18, pady=(0, 18))
        
        admin_title = ctk.CTkLabel(
            admin_frame,
            text="🔑 First Time Setup",
            font=("Segoe UI", 10, "bold"),
            text_color="#ffcc00"
        )
        admin_title.pack(anchor="w", padx=12, pady=(12, 4))
        
        admin_creds = ctk.CTkLabel(
            admin_frame,
            text=(
                "Administrator account:\n"
                "Use the credentials provided during installation.\n"
                "For security, change the admin password after first login."
            ),
            font=("Segoe UI", 9),
            text_color="gray75",
            justify="left"
        )
        admin_creds.pack(anchor="w", padx=12, pady=(0, 12))
        
        # ===== REGISTRATION SECTION =====
        if self.on_register:
            separator = ctk.CTkLabel(container, text="", text_color="gray30")
            separator.pack(pady=8)
            
            register_header = ctk.CTkLabel(
                container,
                text="✨ CREATE NEW ACCOUNT",
                font=("Segoe UI", 14, "bold"),
                text_color="#00ff99"
            )
            register_header.pack(anchor="w", padx=5, pady=(0, 12))
            
            # Registration info box
            register_frame = ctk.CTkFrame(container, fg_color="gray20", corner_radius=12)
            register_frame.pack(fill="x", padx=0, pady=(0, 0))
            
            register_info_text = ctk.CTkLabel(
                register_frame,
                text="Don't have an account yet?\nCreate a new account to get started!",
                font=("Segoe UI", 10),
                text_color="gray85",
                justify="center"
            )
            register_info_text.pack(padx=18, pady=(18, 14))
            
            # Register button
            register_btn = ctk.CTkButton(
                register_frame,
                text="📝 Create New Account",
                font=("Segoe UI", 13, "bold"),
                height=44,
                corner_radius=8,
                fg_color="#00ff99",
                text_color="black",
                hover_color="#00dd77",
                command=self._handle_register
            )
            register_btn.pack(fill="x", padx=18, pady=(0, 18))
        
        # Bind Enter key
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())
    
    def _toggle_password(self):
        """Toggle password visibility."""
        self.show_password = not self.show_password
        if self.show_password:
            self.password_entry.configure(show="")
            self.show_pwd_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="●")
            self.show_pwd_btn.configure(text="👁️")
    
    def _handle_login(self):
        """Handle login button click."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        # Clear previous errors
        self.error_label.configure(text="")
        
        # Validation
        if not username:
            self.error_label.configure(text="❌ Please enter your username")
            return
        
        if not password:
            self.error_label.configure(text="❌ Please enter your password")
            return
        
        # Disable button during login
        self.login_button.configure(state="disabled", text="⏳ Logging in...")
        
        # Call login callback
        try:
            self.on_login_success(username, password, self._on_login_result)
        except Exception as e:
            self._on_login_result(False, f"Error: {str(e)}")
    
    def _on_login_result(self, success: bool, message: str, token: str = None, user: dict = None):
        """
        Handle login result callback.
        
        Args:
            success: Login success status
            message: Result message
            token: JWT token (if successful)
            user: User info dict (if successful)
        """
        if success:
            # Close login window on success
            self.destroy()
        else:
            # Show error and re-enable button
            self.error_label.configure(text=f"❌ {message}")
            self.login_button.configure(state="normal", text="🔓 Login")
    
    def _handle_forgot_password(self):
        """Open the forgot-password wizard."""
        ForgotPasswordWindow(self)

    def _handle_register(self):
        """Handle register button click."""
        if self.on_register:
            self.destroy()
            self.on_register()
    
    def show_error(self, message: str):
        """Show error message."""
        self.error_label.configure(text=f"❌ {message}", text_color="#ff6b7d")
    
    def show_success(self, message: str):
        """Show success message."""
        self.error_label.configure(text=f"✅ {message}", text_color="#00ff99")
