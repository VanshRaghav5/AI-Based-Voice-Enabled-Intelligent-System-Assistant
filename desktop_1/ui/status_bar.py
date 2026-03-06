import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    """Professional status bar showing connection, listening, and processing states."""
    
    def __init__(self, master):
        super().__init__(master, fg_color="#181818", height=30, corner_radius=0)
        
        # Connection status
        self.connection_indicator = ctk.CTkLabel(
            self,
            text="● Offline",
            text_color="#888888",
            font=("Inter", 11)
        )
        self.connection_indicator.pack(side="left", padx=20)
        
        # Listening status
        self.listening_indicator = ctk.CTkLabel(
            self,
            text="",
            text_color="#888888",
            font=("Inter", 11)
        )
        self.listening_indicator.pack(side="left", padx=20)
        
        # Processing status
        self.processing_indicator = ctk.CTkLabel(
            self,
            text="",
            text_color="#888888",
            font=("Inter", 11)
        )
        self.processing_indicator.pack(side="right", padx=20)
    
    def set_connected(self, connected: bool):
        """Update connection status."""
        if connected:
            self.connection_indicator.configure(
                text="● Online",
                text_color="#81C784"
            )
        else:
            self.connection_indicator.configure(
                text="● Offline",
                text_color="#E57373"
            )
    
    def set_listening(self, listening: bool):
        """Update listening status."""
        if listening:
            self.listening_indicator.configure(
                text="● Listening",
                text_color="#64B5F6"
            )
        else:
            self.listening_indicator.configure(text="")
    
    def set_processing(self, processing: bool):
        """Update processing status."""
        if processing:
            self.processing_indicator.configure(
                text="● Working...",
                text_color="#FFD54F"
            )
        else:
            self.processing_indicator.configure(text="")
