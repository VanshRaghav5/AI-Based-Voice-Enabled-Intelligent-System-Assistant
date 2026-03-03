import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    """Professional status bar showing connection, listening, and processing states."""
    
    def __init__(self, master):
        super().__init__(master, fg_color="#1e1e1e", height=40)
        
        # Connection status
        self.connection_indicator = ctk.CTkLabel(
            self,
            text="🔴 Disconnected",
            text_color="#ff4444",
            font=("Arial", 12)
        )
        self.connection_indicator.pack(side="left", padx=15)
        
        # Listening status
        self.listening_indicator = ctk.CTkLabel(
            self,
            text="",
            text_color="#888888",
            font=("Arial", 12)
        )
        self.listening_indicator.pack(side="left", padx=15)
        
        # Processing status
        self.processing_indicator = ctk.CTkLabel(
            self,
            text="",
            text_color="#888888",
            font=("Arial", 12)
        )
        self.processing_indicator.pack(side="right", padx=15)
    
    def set_connected(self, connected: bool):
        """Update connection status.
        
        Args:
            connected: True if connected to backend, False otherwise
        """
        if connected:
            self.connection_indicator.configure(
                text="🟢 Connected",
                text_color="#4CAF50"
            )
        else:
            self.connection_indicator.configure(
                text="🔴 Disconnected",
                text_color="#ff4444"
            )
    
    def set_listening(self, listening: bool):
        """Update listening status.
        
        Args:
            listening: True if microphone is active, False otherwise
        """
        if listening:
            self.listening_indicator.configure(
                text="🎤 Listening...",
                text_color="#2196F3"
            )
        else:
            self.listening_indicator.configure(text="")
    
    def set_processing(self, processing: bool):
        """Update processing status.
        
        Args:
            processing: True if command is being processed, False otherwise
        """
        if processing:
            self.processing_indicator.configure(
                text="⚙ Processing...",
                text_color="#FFA500"
            )
        else:
            self.processing_indicator.configure(text="")
