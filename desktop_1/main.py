"""
OmniAssist AI - Chat-Based Interface

Voice-enabled AI assistant with chat window interface.
"""
import customtkinter as ctk
from ui.chat_window import ChatWindow

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Otto")
app.geometry("900x600")

chat = ChatWindow(app)
chat.pack(fill="both", expand=True)

print("═" * 60)
print("  OmniAssist AI - Chat Interface")
print("═" * 60)
print("")
print("  Features:")
print("    • Type commands or use voice input")
print("    • Click 🎙 Start Listening for voice mode")
print("    • Siri-style overlay with glowing orb")
print("    • Real-time audio visualization")
print("")
print("═" * 60)

app.mainloop()  