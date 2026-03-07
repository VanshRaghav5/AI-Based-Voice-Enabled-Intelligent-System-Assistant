import customtkinter as ctk
from ..services.api_client import send_confirmation

def show_confirmation(master, message):
    popup = ctk.CTkToplevel(master)
    popup.title("Confirmation Required")
    popup.geometry("400x200")

    label = ctk.CTkLabel(popup, text=message)
    label.pack(pady=20)

    yes_btn = ctk.CTkButton(
        popup, text="Yes",
        command=lambda: confirm(popup, True)
    )
    yes_btn.pack(side="left", padx=20)

    no_btn = ctk.CTkButton(
        popup, text="No",
        command=lambda: confirm(popup, False)
    )
    no_btn.pack(side="right", padx=20)

def confirm(popup, approved):
    send_confirmation(approved)
    popup.destroy()