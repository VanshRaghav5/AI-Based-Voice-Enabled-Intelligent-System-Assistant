import customtkinter as ctk
from services.api_client import process_command, start_listening, stop_listening
from services.socket_client import sio, connect, is_connected
from ui.confirmation_popup import show_confirmation
from ui.status_bar import StatusBar

class ChatWindow(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        # Scrollable frame for chat bubbles
        self.chat_scroll = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a")
        self.chat_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Input area frame
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=5)

        self.entry = ctk.CTkEntry(input_frame, placeholder_text="Type your command here...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.send_command())

        self.send_btn = ctk.CTkButton(input_frame, text="Send", width=80, command=self.send_command)
        self.send_btn.pack(side="right")

        # Control buttons frame
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(fill="x", padx=10, pady=5)

        self.listen_btn = ctk.CTkButton(controls_frame, text="Start Listening", command=self.toggle_listen)
        self.listen_btn.pack(side="left", padx=5)

        # Professional status bar at bottom
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side="bottom", fill="x")

        self.listening = False

        self.setup_socket()
        self.attempt_connection()
        
        # Track processing timeout
        self.processing_timeout_id = None

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
        
        # Set timeout to re-enable input if no response (30 seconds)
        if self.processing_timeout_id:
            self.after_cancel(self.processing_timeout_id)
        self.processing_timeout_id = self.after(30000, self._on_processing_timeout)
        
        # Process command in background thread to avoid blocking UI
        import threading
        threading.Thread(target=self._process_command_async, args=(cmd,), daemon=True).start()
    
    def _process_command_async(self, cmd):
        """Process command asynchronously to avoid blocking UI."""
        try:
            process_command(cmd)
        except Exception as e:
            # If HTTP request fails, emit error via socket (if backend is down, this won't work)
            # So we also handle it locally
            self.after(0, lambda: self._on_command_error(str(e)))
    
    def _on_command_error(self, error_msg):
        """Handle command processing error."""
        self.add_message(f"❌ Error: {error_msg}", sender="system")
        self._reset_input_state()
    
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
            self.listen_btn.configure(text="Stop Listening", fg_color="red")
            self.status_bar.set_listening(True)
            self.add_message("🎤 Listening started...", sender="system")
        else:
            stop_listening()
            self.listen_btn.configure(text="Start Listening", fg_color="#1f6aa5")
            self.status_bar.set_listening(False)
            self.add_message("🎤 Listening stopped.", sender="system")
        self.listening = not self.listening

    def setup_socket(self):
        @sio.on("voice_input")
        def on_voice(data):
            text = data.get('text', data) if isinstance(data, dict) else data
            self.add_message(f"🎤 Heard: {text}", sender="system")

        @sio.on("command_result")
        def on_result(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            self.add_message(msg, sender="assistant")
            self._reset_input_state()

        @sio.on("error")
        def on_error(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            self.add_message(f"❌ Error: {msg}", sender="system")
            self._reset_input_state()
    
        @sio.on("execution_step")
        def on_execution_step(data):
            """Handle individual step execution in multi-step plans."""
            step_num = data.get('step', '')
            step_desc = data.get('description', str(data))
            status = data.get('status', 'running')  # running, success, failed
            
            if status == 'success':
                icon = "✅"
            elif status == 'failed':
                icon = "❌"
            else:
                icon = "🔹"
            
            self.add_message(f"{icon} Step {step_num}: {step_desc}", sender="step")
        
        @sio.on("confirmation_required")
        def on_confirm(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            show_confirmation(self, msg)
        
        @sio.on("listening_status")
        def on_listening_status(data):
            is_listening = data.get('listening', False)
            self.status_bar.set_listening(is_listening)
            if is_listening:
                self.listen_btn.configure(text="Stop Listening", fg_color="red")
                self.listening = True
            else:
                self.listen_btn.configure(text="Start Listening", fg_color="#1f6aa5")
                self.listening = False
        
        @sio.on("connect")
        def on_connect():
            self.status_bar.set_connected(True)
            self.add_message("✓ Reconnected to backend.", sender="system")
        
        @sio.on("disconnect")
        def on_disconnect():
            self.status_bar.set_connected(False)
            self.status_bar.set_listening(False)
            self.status_bar.set_processing(False)
            self.add_message("⚠ Disconnected from backend.", sender="system")
    
    def add_message(self, text, sender="assistant"):
        """Add a message bubble to the chat area.
        
        Args:
            text: The message text to display
            sender: One of 'user', 'assistant', 'system', 'thinking', or 'step'
        """
        # Create container frame for alignment
        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", pady=3)

        if sender == "user":
            # User messages: blue bubble, right-aligned
            bubble = ctk.CTkFrame(container, fg_color="#2B5EFF", corner_radius=15)
            bubble.pack(anchor="e", padx=10)
            
            label = ctk.CTkLabel(
                bubble,
                text=f"🧑 You\n{text}",
                text_color="white",
                justify="right",
                wraplength=400,
                padx=15,
                pady=10
            )
            label.pack()
            
        elif sender == "assistant":
            # Assistant messages: dark gray bubble, left-aligned
            bubble = ctk.CTkFrame(container, fg_color="#2d2d2d", corner_radius=15)
            bubble.pack(anchor="w", padx=10)
            
            label = ctk.CTkLabel(
                bubble,
                text=f"🤖 Assistant\n{text}",
                text_color="#4CAF50",
                justify="left",
                wraplength=400,
                padx=15,
                pady=10
            )
            label.pack()
            
        elif sender == "thinking":
            # Thinking indicator: purple bubble, centered, smaller
            bubble = ctk.CTkFrame(container, fg_color="#4a148c", corner_radius=10)
            bubble.pack(anchor="center", padx=10)
            
            label = ctk.CTkLabel(
                bubble,
                text=text,
                text_color="#ce93d8",
                justify="center",
                wraplength=400,
                padx=12,
                pady=6,
                font=("Arial", 11, "italic")
            )
            label.pack()
            
        elif sender == "step":
            # Execution step: light gray bubble, left-aligned, compact
            bubble = ctk.CTkFrame(container, fg_color="#1f1f1f", corner_radius=8)
            bubble.pack(anchor="w", padx=30)
            
            label = ctk.CTkLabel(
                bubble,
                text=text,
                text_color="#90CAF9",
                justify="left",
                wraplength=450,
                padx=10,
                pady=5,
                font=("Arial", 10)
            )
            label.pack()
            
        else:
            # System messages: orange, centered
            bubble = ctk.CTkFrame(container, fg_color="#3d2800", corner_radius=10)
            bubble.pack(anchor="center", padx=10)
            
            label = ctk.CTkLabel(
                bubble,
                text=text,
                text_color="#FFA500",
                justify="center",
                wraplength=500,
                padx=12,
                pady=6
            )
            label.pack()
        
        # Auto-scroll to bottom
        self.chat_scroll._parent_canvas.yview_moveto(1.0)    