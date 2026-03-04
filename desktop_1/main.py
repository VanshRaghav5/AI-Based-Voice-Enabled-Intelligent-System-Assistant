import customtkinter as ctk
from ui.chat_window import ChatWindow

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("OmniAssist AI")
app.geometry("900x600")

chat = ChatWindow(app)
chat.pack(fill="both", expand=True)

app.mainloop()  