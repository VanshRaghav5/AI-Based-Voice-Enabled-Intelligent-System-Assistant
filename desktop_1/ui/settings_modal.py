"""Settings modal for OmniAssist UI."""
import customtkinter as ctk


class SettingsModal(ctk.CTkToplevel):
    """Modern settings modal window."""
    
    def __init__(self, parent, settings_manager):
        """Initialize settings modal.
        
        Args:
            parent: Parent window
            settings_manager: SettingsManager instance
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.title("Settings")
        self.geometry("380x420")
        self.resizable(False, False)
        
        # Position next to parent window (don't cover chat)
        self.after(100, lambda: self._position_window(parent))
        # Get current theme from parent
        is_dark = self.settings_manager.get("theme") == "dark"
        bg_color = "#1a1a1a" if is_dark else "#f5f5f5"
        text_color = "#ffffff" if is_dark else "#000000"
        
        self.configure(fg_color=bg_color)
        
        # Main scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=bg_color
        )
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # ============ APPEARANCE SECTION ============
        self._add_section_title(scroll_frame, "🎨 Appearance", text_color)
        
        # Theme toggle
        theme_frame = self._create_setting_row(scroll_frame, "Theme", text_color, bg_color)
        theme_var = ctk.StringVar(value=self.settings_manager.get("theme"))
        
        theme_light = ctk.CTkRadioButton(
            theme_frame,
            text="Light",
            variable=theme_var,
            value="light",
            fg_color="#2B5EFF",
            command=lambda: self._on_theme_change(theme_var.get())
        )
        theme_light.pack(side="left", padx=3)
        
        theme_dark = ctk.CTkRadioButton(
            theme_frame,
            text="Dark",
            variable=theme_var,
            value="dark",
            fg_color="#2B5EFF",
            command=lambda: self._on_theme_change(theme_var.get())
        )
        theme_dark.pack(side="left", padx=3)
        
        self.theme_var = theme_var
        
        # Font size slider
        font_frame = self._create_setting_row(scroll_frame, "Font Size", text_color, bg_color)
        font_size = self.settings_manager.get("font_size", 11)
        
        self.font_size_label = ctk.CTkLabel(
            font_frame,
            text=f"{font_size}pt",
            text_color=text_color,
            font=("Inter", 9)
        )
        self.font_size_label.pack(side="right", padx=5)
        
        font_slider = ctk.CTkSlider(
            font_frame,
            from_=9,
            to=16,
            number_of_steps=7,
            command=self._on_font_size_change,
            button_color="#2B5EFF",
            progress_color="#2B5EFF"
        )
        font_slider.set(font_size)
        font_slider.pack(side="left", fill="x", expand=True, padx=8)
        
        # ============ ASSISTANT SECTION ============
        self._add_section_title(scroll_frame, "🎭 Assistant", text_color)
        
        # Persona selector
        persona_frame = self._create_setting_row(scroll_frame, "Persona", text_color, bg_color)
        self.persona_var = ctk.StringVar(value=self.settings_manager.get("persona"))
        
        persona_menu = ctk.CTkComboBox(
            persona_frame,
            values=["friendly", "professional", "concise", "formal"],
            variable=self.persona_var,
            command=self._on_persona_change,
            fg_color="#252525",
            text_color=text_color,
            dropdown_fg_color="#333333",
            font=("Inter", 9)
        )
        persona_menu.pack(side="right", padx=3, fill="x", expand=True)
        
        # Language selector
        language_frame = self._create_setting_row(scroll_frame, "Language", text_color, bg_color)
        self.language_var = ctk.StringVar(value=self.settings_manager.get("language"))
        
        language_menu = ctk.CTkComboBox(
            language_frame,
            values=["english", "hindi", "hinglish"],
            variable=self.language_var,
            command=self._on_language_change,
            fg_color="#252525",
            text_color=text_color,
            dropdown_fg_color="#333333",
            font=("Inter", 9)
        )
        language_menu.pack(side="right", padx=3, fill="x", expand=True)
        
        # ============ FEATURES SECTION ============
        self._add_section_title(scroll_frame, "⚙️ Features", text_color)
        
        # Memory toggle
        memory_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        memory_frame.pack(fill="x", padx=15, pady=6)
        
        memory_label = ctk.CTkLabel(
            memory_frame,
            text="💾 Conversation Memory",
            text_color=text_color,
            font=("Inter", 10, "bold")
        )
        memory_label.pack(side="left")
        
        self.memory_var = ctk.BooleanVar(value=self.settings_manager.get("memory_enabled"))
        memory_toggle = ctk.CTkSwitch(
            memory_frame,
            text="",
            variable=self.memory_var,
            onvalue=True,
            offvalue=False,
            command=self._on_memory_change,
            progress_color="#2B5EFF"
        )
        memory_toggle.pack(side="right")
        
        # Auto-listen toggle
        listen_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        listen_frame.pack(fill="x", padx=15, pady=6)
        
        listen_label = ctk.CTkLabel(
            listen_frame,
            text="🎙️ Auto-Listen on Start",
            text_color=text_color,
            font=("Inter", 10, "bold")
        )
        listen_label.pack(side="left")
        
        self.listen_var = ctk.BooleanVar(value=self.settings_manager.get("auto_listen"))
        listen_toggle = ctk.CTkSwitch(
            listen_frame,
            text="",
            variable=self.listen_var,
            onvalue=True,
            offvalue=False,
            command=self._on_listen_change,
            progress_color="#2B5EFF"
        )
        listen_toggle.pack(side="right")
        
        # ============ ABOUT SECTION ============
        self._add_section_title(scroll_frame, "ℹ️ About", text_color)
        
        about_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        about_frame.pack(fill="x", padx=15, pady=2)
        
        about_text = ctk.CTkLabel(
            about_frame,
            text="OmniAssist v1.0",
            text_color=text_color,
            font=("Inter", 9),
            justify="left"
        )
        about_text.pack(pady=1)
        
        # ============ BUTTONS ============
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=12, pady=(6, 8))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            fg_color="#2B5EFF",
            hover_color="#1A45D1",
            font=("Inter", 11, "bold"),
            command=self._save_and_close
        )
        save_btn.pack(side="left", padx=3, fill="x", expand=True)
        
        self.on_settings_changed = None
    
    def _position_window(self, parent):
        """Position settings window next to parent (not covering it)."""
        try:
            parent_x = parent.winfo_x()
            parent_width = parent.winfo_width()
            parent_y = parent.winfo_y()
            
            # Position to the right of parent window
            new_x = parent_x + parent_width + 10
            new_y = parent_y
            
            # Ensure it doesn't go off-screen
            screen_width = self.winfo_screenwidth()
            if new_x + 380 > screen_width:
                new_x = parent_x - 390  # Position to left instead
            
            self.geometry(f"+{max(0, new_x)}+{max(0, new_y)}")
        except:
            pass  # Window positioning failed, use default
    
    def _add_section_title(self, parent, title, text_color):
        """Add a section title."""
        label = ctk.CTkLabel(
            parent,
            text=title,
            text_color=text_color,
            font=("Inter", 12, "bold")
        )
        label.pack(fill="x", padx=15, pady=(10, 3))
    
    def _create_setting_row(self, parent, label_text, text_color, bg_color):
        """Create a setting row frame."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=6)
        
        label = ctk.CTkLabel(
            row,
            text=label_text,
            text_color=text_color,
            font=("Inter", 10, "bold")
        )
        label.pack(side="left")
        
        return row
    
    def _on_theme_change(self, theme):
        """Handle theme change (instant)."""
        self.settings_manager.set("theme", theme)
        if self.on_settings_changed:
            self.on_settings_changed("theme", theme)
    
    def _on_font_size_change(self, value):
        """Handle font size change."""
        size = int(float(value))
        self.font_size_label.configure(text=f"{size}pt")
        self.settings_manager.set("font_size", size)
        if self.on_settings_changed:
            self.on_settings_changed("font_size", size)
    
    def _on_persona_change(self, value):
        """Handle persona change."""
        self.settings_manager.set("persona", value)
        if self.on_settings_changed:
            self.on_settings_changed("persona", value)
    
    def _on_language_change(self, value):
        """Handle language change."""
        self.settings_manager.set("language", value)
        if self.on_settings_changed:
            self.on_settings_changed("language", value)
    
    def _on_memory_change(self):
        """Handle memory toggle."""
        value = self.memory_var.get()
        self.settings_manager.set("memory_enabled", value)
        if self.on_settings_changed:
            self.on_settings_changed("memory_enabled", value)
    
    def _on_listen_change(self):
        """Handle auto-listen toggle."""
        value = self.listen_var.get()
        self.settings_manager.set("auto_listen", value)
        if self.on_settings_changed:
            self.on_settings_changed("auto_listen", value)
    
    def _save_and_close(self):
        """Save and close the settings window."""
        self.destroy()
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        if hasattr(self, 'default_settings'):
            for key, value in self.settings_manager.default_settings.items():
                self.settings_manager.set(key, value)
        self.destroy()
