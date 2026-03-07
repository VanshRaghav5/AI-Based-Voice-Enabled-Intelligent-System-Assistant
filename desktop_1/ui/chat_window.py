import customtkinter as ctk
import requests
from services.api_client import process_command, start_listening, stop_listening, update_settings
from services.socket_client import sio, connect, is_connected
from ui.confirmation_popup import show_confirmation
from ui.status_bar import StatusBar
from ui.listening_overlay import ListeningOverlay
from ui.settings_modal import SettingsModal
from audio.mic_visualizer import MicVisualizer
from settings_manager import settings_manager
import threading

class ChatWindow(ctk.CTkFrame):
    def __init__(self, master, on_logout=None):
        # Determine theme
        self.is_dark = settings_manager.get("theme") == "dark"
        bg_color = "#0A0A0A" if self.is_dark else "#F5F5F5"
        
        super().__init__(master, fg_color=bg_color)
        self.master_window = master
        self.settings_manager = settings_manager
        self.on_logout = on_logout

        # Compact top bar with logo and settings
        top_bar = ctk.CTkFrame(self, fg_color="transparent", height=40)
        top_bar.pack(fill="x", padx=10, pady=(5, 0))
        top_bar.pack_propagate(False)  # Maintain fixed height
        
        # Logo and title - more compact
        logo_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        logo_frame.pack(side="left", padx=5)
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="🎙️",
            font=("Inter", 18)
        )
        logo_label.pack(side="left", padx=(0, 5))
        
        title_label = ctk.CTkLabel(
            logo_frame,
            text="OmniAssist",
            text_color="white" if self.is_dark else "#000000",
            font=("Inter", 14, "bold")
        )
        title_label.pack(side="left")
        
        # User info display
        try:
            from services.api_client import load_token
            _, user = load_token()
            if user:
                user_label = ctk.CTkLabel(
                    logo_frame,
                    text=f"  •  {user.get('username', 'User')}",
                    text_color="#4A9EFF" if self.is_dark else "#2B5EFF",
                    font=("Inter", 11, "bold")
                )
                user_label.pack(side="left", padx=(5, 0))
        except Exception as e:
            print(f"Error loading user info: {e}")
        
        # Right side buttons container
        buttons_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        buttons_frame.pack(side="right", padx=5)
        
        # Logout button
        logout_btn = ctk.CTkButton(
            buttons_frame,
            text="🚪 Logout",
            width=80,
            height=32,
            corner_radius=16,
            fg_color="#DC2626" if self.is_dark else "#EF4444",
            hover_color="#B91C1C" if self.is_dark else "#DC2626",
            text_color="white",
            font=("Inter", 11, "bold"),
            command=self._handle_logout
        )
        logout_btn.pack(side="right", padx=3)
        
        # Settings button on the right - smaller and cleaner
        settings_btn = ctk.CTkButton(
            buttons_frame,
            text="⚙",
            width=32,
            height=32,
            corner_radius=16,
            fg_color="#252525" if self.is_dark else "#E0E0E0",
            hover_color="#333333" if self.is_dark else "#D0D0D0",
            text_color="white" if self.is_dark else "#000000",
            font=("Inter", 14),
            command=self._open_settings
        )
        settings_btn.pack(side="right", padx=3)

        # Expanded chat area - more space for messages
        scroll_bg = "#0F0F0F" if self.is_dark else "#FAFAFA"
        self.chat_scroll = ctk.CTkScrollableFrame(self, fg_color=scroll_bg, corner_radius=0)
        self.chat_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Defer welcome message until widget is fully initialized
        self.after(200, self._show_welcome_message)

        # Input area frame - Sleeker integrated look
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=12, pady=(8, 5))

        entry_bg = "#1e1e1e" if self.is_dark else "#FFFFFF"
        entry_text = "#ffffff" if self.is_dark else "#000000"
        entry_border = "#333333" if self.is_dark else "#CCCCCC"
        
        self.entry = ctk.CTkEntry(
            input_frame, 
            placeholder_text="Type your command here...",
            height=45,
            corner_radius=22,
            border_width=1,
            border_color=entry_border,
            fg_color=entry_bg,
            text_color=entry_text,
            font=("Inter", 13)
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_command())

        self.send_btn = ctk.CTkButton(
            input_frame, 
            text="Send", 
            width=100, 
            height=45,
            corner_radius=22,
            fg_color="#2B5EFF",
            hover_color="#1A45D1",
            font=("Inter", 13, "bold"),
            command=self.send_command
        )
        self.send_btn.pack(side="right")

        # Control buttons frame - more compact
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.pack(fill="x", padx=12, pady=(5, 5))

        listen_bg = "#2D2D2D" if self.is_dark else "#E0E0E0"
        listen_hover = "#3A3A3A" if self.is_dark else "#D0D0D0"
        listen_text = "#4A9EFF" if self.is_dark else "#2B5EFF"
        
        self.listen_btn = ctk.CTkButton(
            controls_frame, 
            text="🎙 Start Listening", 
            height=38,
            corner_radius=19,
            fg_color=listen_bg,
            hover_color=listen_hover,
            text_color=listen_text,
            font=("Inter", 12, "bold"),
            border_width=2,
            border_color="#4A9EFF" if self.is_dark else "#2B5EFF",
            command=self.toggle_listen
        )
        self.listen_btn.pack(side="left")

        # Professional status bar at bottom
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side="bottom", fill="x")

        # Initialize Siri Overlay - Use root window (master) as parent for toplevel
        self.overlay = ListeningOverlay(self.master)
        
        # Initialize Mic Visualizer
        self.mic_visualizer = MicVisualizer(
            callback=lambda amp: self.after(0, lambda: self.overlay.set_amplitude(amp))
        )
        
        self.listening = False

        self.setup_socket()
        # Delay connection until main loop starts (fixes threading issue)
        self.after(100, self.attempt_connection)
        
        # Track processing timeout
        self.processing_timeout_id = None

        # Animation state tracking
        self.pulse_ids = {} # {widget_id: after_id}
        self.typewriter_ids = {} # {label_id: after_id}
    
    def _open_settings(self):
        """Open the settings modal."""
        settings_window = SettingsModal(self.master_window, self.settings_manager)
        settings_window.on_settings_changed = self._on_settings_changed
    
    def _handle_logout(self):
        """Handle logout action."""
        from services.api_client import clear_token
        
        # Disconnect from backend
        from services.socket_client import disconnect
        disconnect()
        
        # Clear authentication token
        clear_token()
        
        # Stop any active listening
        if self.listening:
            self.mic_visualizer.stop()
            if hasattr(self, 'overlay'):
                self.overlay.hide()
        
        print("👋 Logged out successfully")
        
        # Call logout callback if provided
        if self.on_logout:
            self.on_logout()
    
    def _on_settings_changed(self, setting_key, value):
        """Handle settings changes (instant, no restart needed)."""
        if setting_key == "theme":
            # Apply theme change instantly (UI only)
            self._apply_theme_change(value)
        elif setting_key == "font_size":
            # Update font sizes dynamically (UI only)
            self._apply_font_size(value)
        elif setting_key in ["persona", "language", "memory_enabled"]:
            # Send to backend for processing
            self._sync_setting_to_backend(setting_key, value)
    
    def _sync_setting_to_backend(self, setting_key, value):
        """Send setting change to backend API."""
        try:
            if not is_connected():
                self.add_message("⚠ Cannot update backend settings: not connected", sender="system")
                return
            
            # Map frontend setting names to backend names
            backend_settings = {setting_key: value}
            
            # Send to backend
            response = update_settings(backend_settings)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for errors in response
                if result.get('errors'):
                    error_msg = '; '.join(result['errors'])
                    self.add_message(f"⚠ Failed to update {setting_key}: {error_msg}", sender="system")
                    return
                
                # Show success message
                if setting_key == "persona":
                    self.add_message(f"✓ Persona changed to: {value.capitalize()}", sender="system")
                elif setting_key == "language":
                    self.add_message(f"✓ Language changed to: {value.capitalize()}", sender="system")
                elif setting_key == "memory_enabled":
                    status = "enabled" if value else "disabled"
                    self.add_message(f"✓ Memory {status}", sender="system")
            else:
                # Try to get error message from response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Unknown error')
                except:
                    error_msg = f"HTTP {response.status_code}"
                self.add_message(f"⚠ Failed to update {setting_key}: {error_msg}", sender="system")
                
        except Exception as e:
            self.add_message(f"⚠ Error updating {setting_key}: {str(e)}", sender="system")
    
    def _apply_theme_change(self, theme):
        """Apply theme change instantly without restart."""
        self.is_dark = theme == "dark"
        ctk.set_appearance_mode(theme)
        
        # Update main background
        bg_color = "#0A0A0A" if self.is_dark else "#F5F5F5"
        self.configure(fg_color=bg_color)
        
        # Update chat scroll background
        scroll_bg = "#0F0F0F" if self.is_dark else "#FAFAFA"
        self.chat_scroll.configure(fg_color=scroll_bg)
        
        # Update input field colors
        entry_bg = "#1e1e1e" if self.is_dark else "#FFFFFF"
        entry_text = "#ffffff" if self.is_dark else "#000000"
        entry_border = "#333333" if self.is_dark else "#CCCCCC"
        
        self.entry.configure(
            fg_color=entry_bg,
            text_color=entry_text,
            border_color=entry_border
        )
        
        # Update listen button colors
        listen_bg = "#2D2D2D" if self.is_dark else "#E0E0E0"
        listen_hover = "#3A3A3A" if self.is_dark else "#D0D0D0"
        listen_text = "#4A9EFF" if self.is_dark else "#2B5EFF"
        
        self.listen_btn.configure(
            fg_color=listen_bg,
            hover_color=listen_hover,
            text_color=listen_text,
            border_color="#4A9EFF" if self.is_dark else "#2B5EFF"
        )
        
        self.add_message(f"✓ Theme changed to {theme.capitalize()}", sender="system")
    
    def _apply_font_size(self, size):
        """Apply font size change dynamically."""
        # Would need to update all text elements
        # For now, just show confirmation
        self.add_message(f"✓ Font size changed to {size}pt", sender="system")

    def attempt_connection(self):
        """Try to connect to backend and update UI accordingly."""
        success = connect()
        if success:
            self.status_bar.set_connected(True)
            self.add_message("✓ Connected to backend. Ready to assist!", sender="system")
        else:
            self.status_bar.set_connected(False)
            self.add_message(
                "⚠ Cannot connect to backend.\nPlease start the backend server first:\n> python backend\\api_service.py",
                sender="system"
            )

    def send_command(self):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        
        if not is_connected():
            self.add_message("⚠ Not connected to backend. Retrying...", sender="system")
            self.attempt_connection()
            if not is_connected():
                return
        
        # Show user message
        self.add_message(cmd, sender="user")
        self.add_message("🤔 Assistant is thinking...", sender="thinking")
        
        # Clear and disable input
        self.entry.delete(0, "end")
        self.entry.update()  # Force UI update
        self.send_btn.configure(state="disabled", text="Processing...")
        self.entry.configure(state="disabled")
        self.status_bar.set_processing(True)
        
        # Set timeout to re-enable input if no response (3 minutes for LLM + confirmation + email)
        if self.processing_timeout_id:
            self.after_cancel(self.processing_timeout_id)
        self.processing_timeout_id = self.after(180000, self._on_processing_timeout)
        
        # Process command in background thread to avoid blocking UI
        import threading
        threading.Thread(target=self._process_command_async, args=(cmd,), daemon=True).start()
    
    def _process_command_async(self, cmd):
        """Process command asynchronously to avoid blocking UI."""
        try:
            response = process_command(cmd)
            # Check if request succeeded
            if response.status_code != 200:
                error_msg = response.json().get('message', 'Command processing failed')
                self.after(0, lambda: self._on_command_error(error_msg))
        except requests.exceptions.Timeout:
            self.after(0, lambda: self._on_command_error("Request timed out. The operation may still be processing."))
        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self._on_command_error("Cannot connect to backend. Please ensure it's running."))
        except Exception as e:
            # If HTTP request fails, emit error via socket (if backend is down, this won't work)
            # So we also handle it locally
            self.after(0, lambda: self._on_command_error(str(e)))
    
    def _on_command_error(self, error_msg):
        """Handle command processing error."""
        self.after(0, lambda: self.add_message(f"❌ Error: {error_msg}", sender="system"))
        self.after(0, self._reset_input_state)
    
    def _on_processing_timeout(self):
        """Handle timeout if backend doesn't respond."""
        self.add_message("⚠ Request timed out. Backend may be slow or unresponsive.", sender="system")
        self._reset_input_state()
    
    def _reset_input_state(self):
        """Reset input field and button to normal state."""
        # Cancel timeout if active
        if self.processing_timeout_id:
            self.after_cancel(self.processing_timeout_id)
            self.processing_timeout_id = None
        
        # Re-enable input
        self.send_btn.configure(state="normal", text="Send")
        self.entry.configure(state="normal")
        self.entry.focus()
        self.status_bar.set_processing(False)

    def toggle_listen(self):
        if not is_connected():
            self.add_message("⚠ Cannot start listening: backend not connected.", sender="system")
            self.attempt_connection()
            return
        
        if not self.listening:
            start_listening()
            self._update_listening_ui(True)
        else:
            stop_listening()
            self._update_listening_ui(False)

    def _update_listening_ui(self, is_listening):
        """Update listening indicators and overlay in a thread-safe way."""
        try:
            self.status_bar.set_listening(is_listening)
            self.listening = is_listening
            
            if is_listening:
                self.listen_btn.configure(
                    text="⏹ Stop Listening", 
                    fg_color="#DC2626", 
                    hover_color="#B91C1C",
                    text_color="white",
                    border_color="#DC2626"
                )
                if hasattr(self, 'overlay'):
                    self.overlay.show()
                self.mic_visualizer.start()
            else:
                listen_bg = "#2D2D2D" if self.is_dark else "#E0E0E0"
                listen_hover = "#3A3A3A" if self.is_dark else "#D0D0D0"
                listen_text = "#4A9EFF" if self.is_dark else "#2B5EFF"
                self.listen_btn.configure(
                    text="🎙 Start Listening", 
                    fg_color=listen_bg, 
                    hover_color=listen_hover,
                    text_color=listen_text,
                    border_color="#4A9EFF" if self.is_dark else "#2B5EFF"
                )
                if hasattr(self, 'overlay'):
                    self.overlay.hide()
                self.mic_visualizer.stop()
        except Exception as e:
            print(f"Error updating listening UI: {e}")
    
    def _safe_ui_update(self, callback):
        """Safely schedule a UI update from any thread."""
        try:
            if self.winfo_exists():
                self.after(0, callback)
        except RuntimeError:
            # Main loop not running yet, ignore
            pass
        except Exception as e:
            print(f"Error scheduling UI update: {e}")

    def setup_socket(self):
        @sio.on("voice_input")
        def on_voice(data):
            text = data.get('text', data) if isinstance(data, dict) else data
            self._safe_ui_update(lambda: self.overlay.update_transcript(text))
            # When we receive final transcription, transition to PROCESSING
            is_final = data.get('final', False) if isinstance(data, dict) else False
            if is_final:
                self._safe_ui_update(lambda: self.overlay.set_processing())
                self._safe_ui_update(self.mic_visualizer.stop)

        @sio.on("command_result")
        def on_result(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            # Transition overlay: LISTENING → RESPONDING (fade-out)
            self._safe_ui_update(lambda: self.overlay.set_responding())
            self._safe_ui_update(self.mic_visualizer.stop)
            self._safe_ui_update(lambda: self._update_listening_ui(False))
            self._safe_ui_update(lambda: self.add_message(msg, sender="assistant", animate=True))
            self._safe_ui_update(self._reset_input_state)

        @sio.on("error")
        def on_error(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            self._safe_ui_update(lambda: self.overlay.set_responding())
            self._safe_ui_update(self.mic_visualizer.stop)
            self._safe_ui_update(lambda: self._update_listening_ui(False))
            self._safe_ui_update(lambda: self.add_message(f"❌ Error: {msg}", sender="system"))
            self._safe_ui_update(self._reset_input_state)
    
        @sio.on("execution_step")
        def on_execution_step(data):
            step_num = data.get('step', '')
            step_desc = data.get('description', str(data))
            status = data.get('status', 'running')
            
            icon = "✅" if status == 'success' else "❌" if status == 'failed' else "🔹"
            self._safe_ui_update(lambda: self.add_message(f"{icon} Step {step_num}: {step_desc}", sender="step"))
        
        @sio.on("confirmation_required")
        def on_confirm(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            self._safe_ui_update(lambda: self.overlay.set_responding())
            self._safe_ui_update(self.mic_visualizer.stop)
            self._safe_ui_update(lambda: self._update_listening_ui(False))
            # Don't reset input state - keep "Processing..." until confirmed
            self._safe_ui_update(lambda: self.add_message("⏸ Waiting for confirmation...", sender="system"))
            self._safe_ui_update(lambda: show_confirmation(self, msg))

        @sio.on("confirmation_result")
        def on_confirmation_result(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else str(data)
            status = data.get('status', '') if isinstance(data, dict) else ''

            self._safe_ui_update(lambda: self.overlay.set_responding())
            self._safe_ui_update(self.mic_visualizer.stop)
            self._safe_ui_update(lambda: self._update_listening_ui(False))

            if status == 'success':
                self._safe_ui_update(lambda: self.add_message(msg, sender="assistant", animate=True))
            else:
                self._safe_ui_update(lambda: self.add_message(f"❌ {msg}", sender="system"))

            self._safe_ui_update(self._reset_input_state)
        
        @sio.on("listening_status")
        def on_listening_status(data):
            is_listening = data.get('listening', False)
            self._safe_ui_update(lambda: self._update_listening_ui(is_listening))
        
        @sio.on("assistant_shutdown")
        def on_shutdown(data):
            msg = data.get('message', 'Shutting down assistant') if isinstance(data, dict) else str(data)
            self._safe_ui_update(lambda: self.overlay.set_responding())
            self._safe_ui_update(self.mic_visualizer.stop)
            self._safe_ui_update(lambda: self._update_listening_ui(False))
            self._safe_ui_update(lambda: self.add_message(f"👋 {msg}", sender="system"))
            # Close the application after 1 second
            self._safe_ui_update(lambda: self.after(1000, self._shutdown_application))
        
        @sio.on("connect")
        def on_connect():
            self._safe_ui_update(lambda: self.status_bar.set_connected(True))
            self._safe_ui_update(lambda: self.add_message("✓ Connected to backend.", sender="system"))
        
        @sio.on("disconnect")
        def on_disconnect():
            self._safe_ui_update(lambda: self.status_bar.set_connected(False))
            self._safe_ui_update(self._clear_status_indicators)
            self._safe_ui_update(lambda: self.add_message("⚠ Disconnected from backend.", sender="system"))
    
    def _shutdown_application(self):
        """Shutdown the application gracefully."""
        try:
            print("[App] Shutting down application")
            # Stop listening if active
            if self.listening:
                self.mic_visualizer.stop()
            # Close overlay
            if hasattr(self, 'overlay'):
                self.overlay.destroy()
            # Disconnect from backend
            from services.socket_client import disconnect
            disconnect()
            # Quit the application
            self.master_window.quit()
            self.master_window.destroy()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            # Force quit anyway
            import sys
            sys.exit(0)

    def _clear_status_indicators(self):
        """Reset status indicators on disconnect."""
        self.status_bar.set_listening(False)
        self.status_bar.set_processing(False)
        listen_bg = "#2D2D2D" if self.is_dark else "#E0E0E0"
        listen_hover = "#3A3A3A" if self.is_dark else "#D0D0D0"
        listen_text = "#4A9EFF" if self.is_dark else "#2B5EFF"
        self.listen_btn.configure(
            text="🎙 Start Listening", 
            fg_color=listen_bg, 
            hover_color=listen_hover,
            text_color=listen_text,
            border_color="#4A9EFF" if self.is_dark else "#2B5EFF"
        )
        self.listening = False
        if hasattr(self, 'overlay'):
            self.overlay.hide()
        if hasattr(self, 'mic_visualizer'):
            self.mic_visualizer.stop()
    
    def _show_welcome_message(self):
        """Display welcome message when chat starts."""
        try:
            welcome_text = (
                "👋 Hello! I'm OmniAssist, your AI assistant.\n\n"
                "I can help you with:\n"
                "  • Opening applications\n"
                "  • Web searches and browsing\n"
                "  • System commands\n"
                "  • File management\n"
                "  • Answering questions\n\n"
                "Try saying \"open WhatsApp\" or type your command below!"
            )
            self.add_message(welcome_text, sender="assistant")
        except Exception as e:
            print(f"Error showing welcome message: {e}")
    
    def add_message(self, text, sender="assistant", animate=False):
        """Add a message bubble to the chat area with avatar.
        
        Args:
            text: The message text to display
            sender: One of 'user', 'assistant', 'system', 'thinking', or 'step'
            animate: Whether to use a typewriter animation (only for 'assistant')
        """
        try:
            # Create container frame for alignment
            container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
            container.pack(fill="x", pady=6, padx=10)

            if sender == "user":
                # User messages: Clean blue gradient, right-aligned with avatar
                msg_frame = ctk.CTkFrame(container, fg_color="transparent")
                msg_frame.pack(side="right", fill="x")
                
                # Avatar
                avatar = ctk.CTkLabel(
                    msg_frame,
                    text="👤",
                    font=("Inter", 20),
                    width=30
                )
                avatar.pack(side="right", padx=(8, 0))
                
                # Message bubble
                bubble = ctk.CTkFrame(msg_frame, fg_color="#2B5EFF", corner_radius=18)
                bubble.pack(side="right", padx=(0, 5))
                
                label = ctk.CTkLabel(
                    bubble,
                    text=text,
                    text_color="white",
                    wraplength=380,
                    padx=16,
                    pady=11,
                    font=("Inter", 13),
                    justify="left",
                    anchor="w"
                )
                label.pack()
                
            elif sender == "assistant":
                # Assistant messages: Dark with accent border, left-aligned with avatar
                msg_frame = ctk.CTkFrame(container, fg_color="transparent")
                msg_frame.pack(side="left", fill="x")
                
                # Avatar
                avatar = ctk.CTkLabel(
                    msg_frame,
                    text="🤖",
                    font=("Inter", 20),
                    width=30
                )
                avatar.pack(side="left", padx=(0, 8))
                
                # Message bubble with border accent
                bubble = ctk.CTkFrame(
                    msg_frame, 
                    fg_color="#1A1A1A", 
                    corner_radius=18,
                    border_width=2,
                    border_color="#3A3A3A"
                )
                bubble.pack(side="left", padx=(5, 0))
                
                label = ctk.CTkLabel(
                    bubble,
                    text="" if animate else text,
                    text_color="#E8E8E8",
                    wraplength=380,
                    padx=16,
                    pady=11,
                    font=("Inter", 13),
                    justify="left",
                    anchor="w"
                )
                label.pack()
                
                if animate:
                    self._animate_typewriter(label, text)
                
            elif sender == "thinking":
                # Thinking indicator with animation
                msg_frame = ctk.CTkFrame(container, fg_color="transparent")
                msg_frame.pack(side="left", padx=38)
                
                bubble = ctk.CTkFrame(
                    msg_frame, 
                    fg_color="#1A1235", 
                    corner_radius=15, 
                    border_width=2, 
                    border_color="#7C3AED"
                )
                bubble.pack()
                
                label = ctk.CTkLabel(
                    bubble,
                    text=f"✨ {text}",
                    text_color="#D8B4FE",
                    padx=18,
                    pady=10,
                    font=("Inter", 12, "italic")
                )
                label.pack()
                self._add_pulse_animation(bubble, "#5B21B6", "#A78BFA")
                
            elif sender == "step":
                # Step execution indicator - compact
                msg_frame = ctk.CTkFrame(container, fg_color="transparent")
                msg_frame.pack(side="left", padx=48)
                
                label = ctk.CTkLabel(
                    msg_frame,
                    text=f"▸ {text}",
                    text_color="#60A5FA",
                    font=("Inter", 11)
                )
                label.pack(anchor="w")
                
            else:
                # System notifications - centered
                bubble = ctk.CTkFrame(
                    container, 
                    fg_color="#1F1F1F", 
                    corner_radius=12, 
                    border_width=1, 
                    border_color="#996320"
                )
                bubble.pack(pady=2)
                
                label = ctk.CTkLabel(
                    bubble,
                    text=text,
                    text_color="#FFA726",
                    padx=16,
                    pady=9,
                    font=("Inter", 11, "bold")
                )
                label.pack()
            
            # Safe scroll to bottom
            self.after(100, self._scroll_to_bottom)
            
        except Exception as e:
            print(f"Error adding message ({sender}): {e}")

    def _scroll_to_bottom(self):
        """Delayed scroll to bottom to ensure UI has rendered."""
        try:
            if hasattr(self.chat_scroll, "_parent_canvas"):
                self.chat_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _animate_typewriter(self, label, full_text, current_index=0):
        """Assistant message typewriter animation."""
        if current_index <= len(full_text):
            label.configure(text=full_text[:current_index])
            # Auto-scroll during typing
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
            
            # 20-40ms delay for a natural feel
            delay = 30 
            item_id = str(label)
            self.typewriter_ids[item_id] = self.after(delay, lambda: self._animate_typewriter(label, full_text, current_index + 1))
        else:
            item_id = str(label)
            self.typewriter_ids.pop(item_id, None)

    def _add_pulse_animation(self, widget, color1, color2, step=0):
        """Border pulse animation for thinking state."""
        if not widget.winfo_exists():
            return
            
        # Interpolate between two colors (simple 10-step pulse)
        steps = 15
        if step < steps:
            # Towards color2
            r1, g1, b1 = self._hex_to_rgb(color1)
            r2, g2, b2 = self._hex_to_rgb(color2)
            
            r = int(r1 + (r2 - r1) * (step / steps))
            g = int(g1 + (g2 - g1) * (step / steps))
            b = int(b1 + (b2 - b1) * (step / steps))
            
            current_color = self._rgb_to_hex(r, g, b)
            widget.configure(border_color=current_color)
            
            item_id = str(widget)
            self.pulse_ids[item_id] = self.after(50, lambda: self._add_pulse_animation(widget, color1, color2, step + 1))
        elif step < steps * 2:
            # Back to color1
            r1, g1, b1 = self._hex_to_rgb(color2)
            r2, g2, b2 = self._hex_to_rgb(color1)
            
            s = step - steps
            r = int(r1 + (r2 - r1) * (s / steps))
            g = int(g1 + (g2 - g1) * (s / steps))
            b = int(b1 + (b2 - b1) * (s / steps))
            
            current_color = self._rgb_to_hex(r, g, b)
            widget.configure(border_color=current_color)
            
            item_id = str(widget)
            self.pulse_ids[item_id] = self.after(50, lambda: self._add_pulse_animation(widget, color1, color2, step + 1))
        else:
            # Restart
            self._add_pulse_animation(widget, color1, color2, 0)

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, r, g, b):
        return f'#{r:02x}{g:02x}{b:02x}'