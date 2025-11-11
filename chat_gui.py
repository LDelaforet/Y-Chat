import customtkinter as ctk
from tkinter import messagebox

class ChatGUI:
    def __init__(self, master, sendHook=None):
        # === CONFIG THÈME CLAIR ===
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.master = master
        self.sendHook = sendHook if sendHook else lambda msg: print("[sendHook]", msg)

        self.channels = {}
        self.friends = {}
        self.current_view_name = None
        self.current_view_type = None

        # === COULEURS ===
        self.color_text = "#1E1E1E"
        self.color_active = "#0078D7"
        self.color_unread = "#D83B01"

        self._build_ui()

    # ------------------------
    # Construction de l'interface
    # ------------------------
    def _build_ui(self):
        self.master.title("Chat Client - Light Mode")
        self.master.geometry("1100x700")

        # === PANNEAU GAUCHE ===
        left_panel = ctk.CTkFrame(self.master, width=280, corner_radius=12)
        left_panel.pack(side="left", fill="y", padx=8, pady=8)

        ctk.CTkLabel(left_panel, text="Amis", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.friends_frame = self._make_scrollable_frame(left_panel)
        self.friends_frame.pack(fill="both", expand=True, padx=6, pady=(0, 12))

        ctk.CTkLabel(left_panel, text="Channels", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=10, pady=(6, 6))
        self.channels_frame = self._make_scrollable_frame(left_panel)
        self.channels_frame.pack(fill="both", expand=True, padx=6, pady=(0, 12))

        # === PANNEAU CENTRAL ===
        center_panel = ctk.CTkFrame(self.master, corner_radius=12)
        center_panel.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self.header_var = ctk.StringVar(value="Aucune conversation sélectionnée")
        ctk.CTkLabel(center_panel, textvariable=self.header_var,
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=self.color_active).pack(anchor="w", padx=16, pady=(12, 8))

        # Zone messages
        self.msg_box = ctk.CTkTextbox(center_panel, height=400,
                                      font=("Consolas", 14),
                                      corner_radius=10, wrap="word")
        self.msg_box.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.msg_box.configure(state="disabled")

        # Barre d'envoi
        bottom = ctk.CTkFrame(center_panel, fg_color=("white", "#f2f2f2"), corner_radius=10)
        bottom.pack(fill="x", padx=12, pady=(0, 8))

        self.entry_var = ctk.StringVar()
        self.entry = ctk.CTkEntry(bottom, textvariable=self.entry_var,
                                  placeholder_text="Écrire un message...",
                                  font=ctk.CTkFont(size=14))
        self.entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", lambda e: self._on_send())

        send_btn = ctk.CTkButton(bottom, text="Envoyer", command=self._on_send,
                                 corner_radius=8, font=ctk.CTkFont(size=14, weight="bold"))
        send_btn.pack(side="right", padx=10, pady=10)

    def _make_scrollable_frame(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=10)
        return scroll

    # ------------------------
    # Gestion des channels / amis
    # ------------------------
    def add_channel(self, name):
        if name in self.channels:
            return
        lbl = ctk.CTkButton(self.channels_frame, text=name, anchor="w", fg_color="transparent",
                            text_color=self.color_text, hover_color="#e8e8e8",
                            font=ctk.CTkFont(size=14),
                            command=lambda n=name: self._select("channel", n))
        lbl.pack(fill="x", pady=3, padx=4)
        self.channels[name] = lbl

    def add_friend(self, name):
        if name in self.friends:
            return
        lbl = ctk.CTkButton(self.friends_frame, text=name, anchor="w", fg_color="transparent",
                            text_color=self.color_text, hover_color="#e8e8e8",
                            font=ctk.CTkFont(size=14),
                            command=lambda n=name: self._select("friend", n))
        lbl.pack(fill="x", pady=3, padx=4)
        self.friends[name] = lbl

    def set_channel_active(self, name):
        if name in self.channels:
            self.channels[name].configure(text_color=self.color_active)

    def set_channel_inactive(self, name):
        if name in self.channels:
            self.channels[name].configure(text_color=self.color_text)

    def set_friend_active(self, name):
        if name in self.friends:
            self.friends[name].configure(text_color=self.color_active)

    def set_friend_inactive(self, name):
        if name in self.friends:
            self.friends[name].configure(text_color=self.color_text)

    def remove_channel(self, name):
        if name in self.channels:
            self.channels[name].destroy()
            del self.channels[name]

    def remove_friend(self, name):
        if name in self.friends:
            self.friends[name].destroy()
            del self.friends[name]

    # ------------------------
    # Messages
    # ------------------------
    def add_message(self, author, content):
        self.msg_box.configure(state="normal")
        self.msg_box.insert("end", f"[{author}] {content}\n")
        self.msg_box.see("end")
        self.msg_box.configure(state="disabled")

    def remove_messages(self, count=1):
        self.msg_box.configure(state="normal")
        lines = self.msg_box.get("1.0", "end").splitlines()
        self.msg_box.delete("1.0", "end")
        self.msg_box.insert("1.0", "\n".join(lines[:-count]) + "\n")
        self.msg_box.configure(state="disabled")

    def wipe_messages(self):
        self.msg_box.configure(state="normal")
        self.msg_box.delete("1.0", "end")
        self.msg_box.configure(state="disabled")

    # ------------------------
    # Sélection / envoi
    # ------------------------
    def _select(self, type_, name):
        self.current_view_type = type_
        self.current_view_name = name
        self.header_var.set(f"{'Channel' if type_ == 'channel' else 'Ami'} — {name}")
        for lbl in (self.channels if type_ == "channel" else self.friends).values():
            lbl.configure(text_color=self.color_text)
        if type_ == "channel":
            self.set_channel_active(name)
        else:
            self.set_friend_active(name)
        self.wipe_messages()

    def _on_send(self):
        text = self.entry_var.get().strip()
        if not text:
            return
        try:
            self.sendHook(text)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
        self.add_message("Vous", text)
        self.entry_var.set("")

    # ------------------------
    # Utilitaires
    # ------------------------
    def wipe_all(self):
        for c in list(self.channels.values()):
            c.destroy()
        for f in list(self.friends.values()):
            f.destroy()
        self.channels.clear()
        self.friends.clear()
        self.wipe_messages()

    def current_channel(self):
        if self.current_view_type == "channel":
            return self.current_view_name
        return None


# === Démo ===
if __name__ == "__main__":
    root = ctk.CTk()
    gui = ChatGUI(root, sendHook=lambda msg: print("HOOK:", msg))

    gui.add_channel("général")
    gui.add_channel("dev")
    gui.add_friend("Alice")
    gui.add_friend("Bob")

    gui.channels["dev"].configure(text_color=gui.color_unread)

    root.mainloop()
