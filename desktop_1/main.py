"""
OmniAssist AI - Chat-Based Interface

Voice-enabled AI assistant with chat window interface.
"""
import customtkinter as ctk
from ui.chat_window import ChatWindow
from ui.login_window import LoginWindow
from ui.register_window import RegisterWindow
from settings_manager import settings_manager
from services.api_client import verify_token, login, load_token, register as api_register
import sys

# Load theme from settings
theme = settings_manager.get("theme", "dark")
ctk.set_appearance_mode(theme)
ctk.set_default_color_theme("blue")


class OmniAssistApp:
    """Main application controller with authentication."""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("OmniAssist")
        self.root.geometry("900x600")
        self.root.minsize(700, 500)
        
        # Hide main window initially
        self.root.withdraw()
        
        self.chat_window = None
        self.login_window = None
        self.register_window = None
        
        # Check for existing token
        self._check_authentication()
    
    def _check_authentication(self):
        """Check if user has valid token."""
        token, user = load_token()
        
        if token:
            # Verify token with server
            valid, user_info = verify_token()
            
            if valid:
                print(f"✅ Authenticated as: {user_info.get('username')} ({user_info.get('role')})")
                self._show_main_app()
                return
        
        # No valid token, show login
        self._show_login()
    
    def _show_login(self):
        """Show login window."""
        # Show root window temporarily for login modal
        self.root.deiconify()
        
        self.login_window = LoginWindow(
            parent=self.root,
            on_login_success=self._handle_login,
            on_register=self._show_register
        )
        
        # Hide root again
        self.root.withdraw()
    
    def _show_register(self):
        """Show registration window."""
        # Show root window
        self.root.deiconify()
        
        self.register_window = RegisterWindow(
            parent=self.root,
            on_register_success=self._handle_register,
            on_back=self._show_login
        )
        
        # Hide root again
        self.root.withdraw()
    
    def _handle_login(self, username: str, password: str, callback):
        """
        Handle login attempt.
        
        Args:
            username: Username
            password: Password
            callback: Callback to call with result
        """
        success, message, token, user = login(username, password)
        
        if success:
            print(f"✅ Login successful: {user.get('username')} ({user.get('role')})")
            callback(True, message, token, user)
            self._show_main_app()
        else:
            callback(False, message)
    
    def _handle_register(self, username: str, email: str, password: str, callback):
        """
        Handle registration.
        
        Args:
            username: Username
            email: Email address
            password: Password
            callback: Callback to call with result
        """
        success, message = api_register(username, email, password)
        
        if success:
            print(f"✅ Registration successful: {username}")
            callback(True, message)
            # Go back to login after short delay
            self.root.after(1500, self._show_login)
        else:
            callback(False, message)
    
    def _show_main_app(self):
        """Show main chat application."""
        # Show main window
        self.root.deiconify()
        
        # Create chat window if not exists
        if not self.chat_window:
            self.chat_window = ChatWindow(self.root)
            self.chat_window.pack(fill="both", expand=True)
        
        self._print_startup_banner()
    
    def _print_startup_banner(self):
        """Print startup information."""
        token, user = load_token()
        
        print("═" * 60)
        print("  OmniAssist AI - Chat Interface")
        print("═" * 60)
        print("")
        print(f"  👤 User: {user.get('username')} ({user.get('role')})")
        print("")
        print("  Features:")
        print("    • Type commands or use voice input")
        print("    • Click 🎙 Start Listening for voice mode")
        print("    • Siri-style overlay with glowing orb")
        print("    • Real-time audio visualization")
        print("    • ⚙️ Click settings to customize")
        print("")
        print(f"  Theme: {theme.capitalize()}")
        print("  🔒 Security: Enabled (JWT Authentication)")
        print("═" * 60)
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = OmniAssistApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)