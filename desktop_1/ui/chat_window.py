import customtkinter as ctk
from services.api_client import process_command, start_listening, stop_listening
from services.socket_client import sio, connect, is_connected
from ui.confirmation_popup import show_confirmation

class ChatWindow(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

        self.chat_area = ctk.CTkTextbox(self)
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.entry = ctk.CTkEntry(self, placeholder_text="Type your command here...")
        self.entry.pack(fill="x", padx=10, pady=5)
        self.entry.bind("<Return>", lambda e: self.send_command())

        self.send_btn = ctk.CTkButton(self, text="Send", command=self.send_command)
        self.send_btn.pack(pady=5)

        self.listen_btn = ctk.CTkButton(self, text="Start Listening", command=self.toggle_listen)
        self.listen_btn.pack(pady=5)

        self.status_label = ctk.CTkLabel(self, text="⚠ Disconnected", text_color="orange")
        self.status_label.pack(pady=5)

        self.listening = False

        self.setup_socket()
        self.attempt_connection()

    def attempt_connection(self):
        """Try to connect to backend and update UI accordingly."""
        success = connect()
        if success:
            self.status_label.configure(text="✓ Connected", text_color="green")
            self.chat_area.insert("end", "\n✓ Connected to backend. Ready to assist!\n")
        else:
            self.status_label.configure(text="⚠ Backend not running", text_color="red")
            self.chat_area.insert(
                "end",
                "\n⚠ Cannot connect to backend.\n"
                "   Please start the backend server first:\n"
                "   > python backend\\api_service.py\n\n"
            )

    def send_command(self):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        
        if not is_connected():
            self.chat_area.insert("end", "\n⚠ Not connected to backend. Retrying...\n")
            self.attempt_connection()
            if not is_connected():
                return
        
        self.chat_area.insert("end", f"\n🧑 You: {cmd}\n")
        process_command(cmd)
        self.entry.delete(0, "end")

    def toggle_listen(self):
        if not is_connected():
            self.chat_area.insert("end", "\n⚠ Cannot start listening: backend not connected.\n")
            self.attempt_connection()
            return
        
        if not self.listening:
            start_listening()
            self.listen_btn.configure(text="Stop Listening", fg_color="red")
            self.chat_area.insert("end", "\n🎤 Listening started...\n")
        else:
            stop_listening()
            self.listen_btn.configure(text="Start Listening", fg_color="#1f6aa5")
            self.chat_area.insert("end", "\n🎤 Listening stopped.\n")
        self.listening = not self.listening

    def setup_socket(self):
        @sio.on("voice_input")
        def on_voice(data):
            text = data.get('text', data) if isinstance(data, dict) else data
            self.chat_area.insert("end", f"\n🎤 Heard: {text}\n")

        @sio.on("command_result")
        def on_result(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            self.chat_area.insert("end", f"\n🤖 Assistant: {msg}\n")

        @sio.on("error")
        def on_error(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            self.chat_area.insert("end", f"\n❌ Error: {msg}\n")
    
        @sio.on("confirmation_required")
        def on_confirm(data):
            msg = data.get('message', str(data)) if isinstance(data, dict) else data
            show_confirmation(self, msg)
        
        @sio.on("listening_status")
        def on_listening_status(data):
            is_listening = data.get('listening', False)
            if is_listening:
                self.listen_btn.configure(text="Stop Listening", fg_color="red")
                self.listening = True
            else:
                self.listen_btn.configure(text="Start Listening", fg_color="#1f6aa5")
                self.listening = False
        
        @sio.on("connect")
        def on_connect():
            self.status_label.configure(text="✓ Connected", text_color="green")
            self.chat_area.insert("end", "\n✓ Reconnected to backend.\n")
        
        @sio.on("disconnect")
        def on_disconnect():
            self.status_label.configure(text="⚠ Disconnected", text_color="orange")
            self.chat_area.insert("end", "\n⚠ Disconnected from backend.\n")    