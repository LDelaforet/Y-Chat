import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import asyncio
from datetime import datetime
import queue


class ChatGUI:
    def __init__(self, master, sendHook=None, show_login_at_start=True):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.master = master
        self.sendHook = sendHook
        self.loop = None
        # File d'événements pour les callbacks provenant d'un autre thread
        # Les éléments poussés sont des tuples: (handler, sock, args_list)
        self.event_queue = queue.Queue()

        # État
        self.channels = {}
        self.friends = {}
        self.current_view_name = None
        self.current_view_type = None
        self.username = ""
        self.current_messages = []
        self.is_loading_messages = False

        # Couleurs
        self.color_text = ("#1E1E1E", "white")
        self.color_active = "#0078D7"
        self.color_unread = "#D83B01"
        self.color_asked_friend = "#339966"
        self.color_friend_asked = "#993366"

        self._build_ui()
        # Lancer le polling de la file d'événements (appelé depuis la boucle principale Tk)
        self.master.after(100, self._process_event_queue)

        if show_login_at_start:
            self.master.after(100, self.show_login_sync)

    def send_command(self, commands):
        """Envoie une ou plusieurs commandes au serveur"""
        if not self.sendHook:
            return
            
        if not isinstance(commands, list):
            commands = [commands]
            
        if asyncio.iscoroutinefunction(self.sendHook):
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(
                    lambda: asyncio.create_task(self._send_commands_async(commands))
                )
        else:
            for cmd in commands:
                self.sendHook(self, cmd)

    async def _send_commands_async(self, commands):
        """Envoie les commandes de manière asynchrone avec délai"""
        for cmd in commands:
            await self.sendHook(self, cmd)
            await asyncio.sleep(0.1)

    def set_username(self, username):
        """Définit le nom d'utilisateur et affiche la fenêtre"""
        self.username = username
        self.user_label.configure(text=username)
        
        if username:
            self.master.deiconify()
            self.send_command(["CHANNELLIST", "FRIENDLIST", "ASKEDFRIEND", "FRIENDASKED"])
        else:
            self.master.withdraw()

    def show_login_sync(self):
        """Affiche la popup de connexion"""
        if self.username:
            self.master.deiconify()
            return
        
        # Garder la fenêtre visible mais vide pendant le login
        # (nécessaire pour éviter un bug avec CTkToplevel)
        popup = LoginPopup(self, self.master, self.sendHook)
        self.master.wait_window(popup)
        
        # Si l'utilisateur n'est toujours pas connecté après la popup, cacher la fenêtre
        if not self.username:
            self.master.withdraw()

    def show_connection_sync(self, default_ip="leovelazquez.fr", default_port="484"):
        """Affiche la popup de connexion réseau"""
        if hasattr(self, 'server_ip') and self.server_ip:
            return
        
        # Initialiser les attributs à None pour que main.py puisse les vérifier
        self.server_ip = None
        self.server_port = None
        
        popup = ConnectionPopup(self, self.master, self.sendHook, default_ip, default_port)
        self.master.wait_window(popup)

    def new_msg(self, message, channel_type):
        """Gère l'arrivée d'un nouveau message"""
        channel_name = message["channel"]
        
        # Récupérer le bon dictionnaire (channels ou friends)
        channels_dict = self.channels if channel_type == "public" else self.friends
        
        if channel_name not in channels_dict:
            return
            
        # Si c'est le canal actif, afficher directement
        is_active = (
            self.current_view_name == channel_name and
            ((self.current_view_type == "channel" and channel_type == "public") or
             (self.current_view_type == "friend" and channel_type == "private"))
        )
        
        if is_active:
            self.current_messages.append(message)
            if not self.is_loading_messages:
                self.add_message(message["sender"], message["content"])
        else:
            channels_dict[channel_name]["has_unread"] = True
            self._refresh_colors()

    def _refresh_colors(self):
        """Met à jour les couleurs des boutons selon leur état"""
        for name, data in self.friends.items():
            if data.get("has_unread"):
                self._set_button_color(data["button"], self.color_unread)
            elif data.get("status") == "youAsked":
                self._set_button_color(data["button"], self.color_friend_asked)
            elif data.get("status") == "askedYou":
                self._set_button_color(data["button"], self.color_asked_friend)
        
        for name, data in self.channels.items():
            if data.get("has_unread"):
                self._set_button_color(data["button"], self.color_unread)

    def _set_button_color(self, button, color):
        """Change la couleur du texte d'un bouton"""
        button.configure(text_color=color)

    def _build_ui(self):
        """Construit l'interface utilisateur"""
        self.master.title("Y-Chat")
        self.master.geometry("1100x700")

        # === Panneau gauche ===
        left_panel = ctk.CTkFrame(self.master, width=280, corner_radius=12)
        left_panel.pack(side="left", fill="y", padx=8, pady=8)

        # En-tête Amis
        friends_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        friends_header.pack(fill="x", padx=10, pady=(10, 6))
        ctk.CTkLabel(friends_header, text="Amis", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(friends_header, text="+", command=self._show_friend_popup,
                     corner_radius=8, width=30, font=ctk.CTkFont(size=14, weight="bold")).pack(side="right")

        # Liste amis
        self.friends_frame = ctk.CTkScrollableFrame(left_panel, corner_radius=10)
        self.friends_frame.pack(fill="both", expand=True, padx=6, pady=(0, 12))

        # En-tête Channels
        ctk.CTkLabel(left_panel, text="Channels", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=10, pady=(6, 6))

        # Liste channels
        self.channels_frame = ctk.CTkScrollableFrame(left_panel, corner_radius=10)
        self.channels_frame.pack(fill="both", expand=True, padx=6, pady=(0, 12))

        # Pied de page (username + thème)
        bottom_left = ctk.CTkFrame(left_panel, corner_radius=10, fg_color=("lightgray", "#2b2b2b"))
        bottom_left.pack(fill="x", padx=10, pady=(0, 10))

        self.user_label = ctk.CTkLabel(bottom_left, text=self.username, font=ctk.CTkFont(size=14),
                                       fg_color=("white", "#1E1E1E"), corner_radius=8)
        self.user_label.pack(side="left", fill="x", expand=True, padx=(5, 5), pady=5)

        ctk.CTkButton(bottom_left, text="🌙", width=30, command=self._toggle_theme).pack(
            side="right", padx=(0, 5), pady=5)

        # === Panneau central ===
        center_panel = ctk.CTkFrame(self.master, corner_radius=12)
        center_panel.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        # En-tête avec bouton "Charger plus"
        header_frame = ctk.CTkFrame(center_panel, fg_color="transparent")
        header_frame.pack(fill="x")

        self.header_label = ctk.CTkLabel(header_frame, text="Aucune conversation sélectionnée",
                                        font=ctk.CTkFont(size=20, weight="bold"), text_color=self.color_active)
        self.header_label.pack(side="left", anchor="w", padx=16, pady=(12, 8))

        self.load_more_btn = ctk.CTkButton(header_frame, text="Charger + de messages",
                                          command=self._schedule_load_more, corner_radius=8, width=200,
                                          font=ctk.CTkFont(size=14, weight="bold"))
        self.load_more_btn.pack(side="right", padx=16, pady=(12, 8))
        self.load_more_btn.pack_forget()

        # Zone de messages
        self.msg_box = ctk.CTkTextbox(center_panel, height=600, font=("Consolas", 14),
                                     corner_radius=10, wrap="word")
        self.msg_box.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.msg_box.configure(state="disabled")
        
        # Gestion du scroll
        self._setup_scroll_handlers()

        # Zone de saisie
        bottom = ctk.CTkFrame(center_panel, fg_color=("white", "#1E1E1E"), corner_radius=10)
        bottom.pack(fill="x", padx=12, pady=(0, 8))

        self.entry = ctk.CTkEntry(bottom, placeholder_text="Écrire un message...",
                                 font=ctk.CTkFont(size=14))
        self.entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", lambda e: self._on_send())

        ctk.CTkButton(bottom, text="Envoyer", command=self._on_send, corner_radius=8,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="right", padx=10, pady=10)

    def _setup_scroll_handlers(self):
        """Configure les gestionnaires de défilement"""
        self.msg_box.bind("<Configure>", lambda e: self.master.after(10, self._check_scroll_top))
        
        if hasattr(self.msg_box, "_canvas"):
            canvas = self.msg_box._canvas
            canvas.bind("<Enter>", lambda e: canvas.focus_set())
            canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
            canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    def _check_scroll_top(self):
        """Vérifie si on est en haut pour afficher le bouton 'Charger plus'"""
        try:
            y0, y1 = self.msg_box.yview()
            can_scroll = (y1 - y0) < 0.9999
            at_top = y0 <= 1e-9
            
            if can_scroll and at_top:
                self.load_more_btn.pack(side="right", padx=16, pady=(12, 8))
            else:
                self.load_more_btn.pack_forget()
        except Exception:
            pass

    def _schedule_load_more(self):
        """Planifie le chargement de messages supplémentaires"""
        if asyncio.iscoroutinefunction(self._load_more):
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(lambda: asyncio.create_task(self._load_more()))
        else:
            self._load_more()

    async def _load_more(self):
        """Charge plus de messages pour le canal actuel"""
        self.is_loading_messages = True
        self.load_more_btn.pack_forget()

        # Sauvegarder position de scroll
        old_scroll_pos = 0
        try:
            if hasattr(self.msg_box, "_canvas"):
                old_scroll_pos = self.msg_box._canvas.yview()[0]
        except Exception:
            pass

        # Effacer et recharger
        self.wipe_messages()
        await asyncio.sleep(0.1)

        # Demander plus de messages
        count = len(self.current_messages)
        if self.current_view_type == "friend":
            self.send_command(f"LISTPRIVMSG {self.current_view_name} {count}")
            self.send_command(f"LISTPRIVMSG {self.current_view_name} {count+20}")
        else:
            self.send_command(f"LISTMSG {self.current_view_name} {count}")
            self.send_command(f"LISTMSG {self.current_view_name} {count+20}")

        await asyncio.sleep(0.5)

        # Trier et afficher
        self.current_messages.sort(key=lambda m: datetime.strptime(m["timestamp"], "%Y-%m-%d_%H:%M:%S"))
        
        for msg in self.current_messages:
            self.master.after(0, lambda m=msg: self.add_message(m["sender"], m["content"]))

        # Restaurer scroll
        try:
            if hasattr(self.msg_box, "_canvas"):
                self.master.after(100, lambda: self.msg_box._canvas.yview_moveto(old_scroll_pos))
        except Exception:
            pass

        self.is_loading_messages = False

    def _toggle_theme(self):
        """Bascule entre thème clair et sombre"""
        mode = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Dark" if mode == "Light" else "Light")

    def _show_friend_popup(self):
        """Affiche la popup de demande d'ami"""
        self.master.after(0, lambda: FriendAskPopup(self, self.master, self.sendHook))

    def _process_event_queue(self):
        """Vide la file d'événements et exécute les handlers dans le thread principal."""
        try:
            while True:
                handler, sock, args = self.event_queue.get_nowait()
                try:
                    # Exécuter le handler dans le contexte de la GUI
                    handler(sock, self, *args)
                except Exception as e:
                    print(f"Erreur lors du traitement d'un événement GUI: {e}")
        except queue.Empty:
            pass
        # Re-planifier
        try:
            self.master.after(50, self._process_event_queue)
        except Exception:
            # Si la fenêtre est fermée, ignore
            pass

    def add_message(self, author, content):
        """Ajoute un message à la zone de chat"""
        self.msg_box.configure(state="normal")
        self.msg_box.insert("end", f"[{author}] {content}\n")
        self.msg_box.see("end")
        self.msg_box.configure(state="disabled")

    def add_channel(self, name):
        """Ajoute un canal à la liste"""
        if name in self.channels:
            return

        btn = ctk.CTkButton(
            self.channels_frame, text=name, anchor="w", fg_color="transparent",
            text_color=self.color_text, hover_color=("#e8e8e8", "#242424"),
            font=ctk.CTkFont(size=14), corner_radius=8,
            command=lambda: self._select_view("channel", name)
        )
        btn.pack(fill="x", pady=3, padx=4)
        
        self.channels[name] = {"button": btn, "has_unread": False}

    def add_friend(self, name, status="friend"):
        """Ajoute un ami à la liste"""
        if name in self.friends:
            if status == "friend" and self.friends[name].get("status") != "friend":
                self.remove_friend(name)
            else:
                return

        command = None if status in ["youAsked", "askedYou"] else lambda: self._select_view("friend", name)

        btn = ctk.CTkButton(
            self.friends_frame, text=name, anchor="w", fg_color="transparent",
            text_color=self.color_text, hover_color=("#e8e8e8", "#242424"),
            font=ctk.CTkFont(size=14), corner_radius=8, command=command
        )
        btn.pack(fill="x", pady=3, padx=4)
        
        self.friends[name] = {"button": btn, "has_unread": False, "status": status}
        self._refresh_colors()

    def remove_friend(self, name):
        """Supprime un ami de la liste"""
        if name in self.friends:
            self.friends[name]["button"].destroy()
            del self.friends[name]

    def wipe_messages(self):
        """Efface tous les messages"""
        self.msg_box.configure(state="normal")
        self.msg_box.delete("1.0", "end")
        self.msg_box.configure(state="disabled")

    def _select_view(self, view_type, name):
        """Sélectionne un canal ou un ami"""
        self.current_view_type = view_type
        self.current_view_name = name
        self.header_label.configure(text=f"{'Channel' if view_type == 'channel' else 'Ami'} — {name}")
        
        # Réinitialiser les couleurs
        for data in self.channels.values():
            self._set_button_color(data["button"], self.color_text)
        for data in self.friends.values():
            self._set_button_color(data["button"], self.color_text)
        
        # Activer le canal/ami sélectionné
        target = self.channels if view_type == "channel" else self.friends
        if name in target:
            target[name]["has_unread"] = False
            self._set_button_color(target[name]["button"], self.color_active)
        
        # Charger les messages
        self.wipe_messages()
        self.current_messages = []
        self._schedule_load_more()
        self._refresh_colors()

    def _on_send(self):
        """Envoie un message"""
        if not self.current_view_name:
            return
            
        text = self.entry.get().strip()
        if not text:
            return

        # Envoyer la commande
        if self.current_view_type == "friend":
            self.send_command(f"NEWPRIVMSG {self.current_view_name} {text}")
        else:
            self.send_command(f"NEWMSG {self.current_view_name} {text}")

        # Afficher localement
        self.add_message("Vous", text)
        self.current_messages.append({
            'channel': self.current_view_name,
            'sender': 'Vous',
            'timestamp': datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
            'content': text
        })
        
        self.entry.delete(0, "end")
    
    def _show_warning(self, text):
        """Affiche une boîte d'avertissement avec le texte donné"""
        messagebox.showwarning("Avertissement", text)


class LoginPopup(ctk.CTkToplevel):
    """Popup de connexion/inscription"""
    def __init__(self, parent, master, sendHook):
        super().__init__(master)
        self.sendHook = sendHook
        self.parent = parent
        self.title("Connexion")
        self.geometry("300x260")
        self.resizable(False, False)

        ctk.CTkLabel(self, text="Connexion", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 8))
        
        self.username = ctk.CTkEntry(self, placeholder_text="Nom d'utilisateur")
        self.username.pack(pady=8, padx=20)
        
        self.password = ctk.CTkEntry(self, placeholder_text="Mot de passe", show="*")
        self.password.pack(pady=8, padx=20)

        frame_btn = ctk.CTkFrame(self, fg_color="transparent")
        frame_btn.pack(pady=20)

        ctk.CTkButton(frame_btn, text="Se connecter", width=100, command=self._login).pack(side="left", padx=10)
        ctk.CTkButton(frame_btn, text="S'inscrire", width=100, fg_color="#4CAF50",
                     hover_color="#3b8e40", command=self.register).pack(side="right", padx=10)

        self.username.focus()

    def _login(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()
        
        if not user or not pwd:
            messagebox.showwarning("Erreur", "Merci de remplir tous les champs")
            return
            
        if self.parent.loop:
            asyncio.run_coroutine_threadsafe(
                self.sendHook(self.parent, f"/login {user} {pwd}"),
                self.parent.loop
            )
        self.destroy()

    def register(self):
        user = self.username.get().strip()
        pwd = self.password.get().strip()
        
        if not user or not pwd:
            messagebox.showwarning("Erreur", "Merci de remplir tous les champs")
            return
            
        if self.parent.loop:
            asyncio.run_coroutine_threadsafe(
                self.sendHook(self.parent, f"/register {user} {pwd}"),
                self.parent.loop
            )
        messagebox.showinfo("Succès", "Compte créé ✅")


class FriendAskPopup(ctk.CTkToplevel):
    """Popup pour demander un ami"""
    def __init__(self, parent, master, sendHook):
        super().__init__(master)
        self.sendHook = sendHook
        self.parent = parent
        self.title("Demander un ami")
        self.geometry("260x180")
        self.resizable(False, False)

        ctk.CTkLabel(self, text="Demander un ami", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(15, 8))
        
        self.username = ctk.CTkEntry(self, placeholder_text="Nom d'utilisateur")
        self.username.pack(pady=8, padx=20)

        ctk.CTkButton(self, text="Demander en ami", width=140, command=self._ask_friend).pack(pady=20)

        self.username.focus()

    def _ask_friend(self):
        user = self.username.get().strip()
        
        if not user:
            messagebox.showwarning("Erreur", "Merci de remplir le nom d'utilisateur")
            return
            
        if self.parent.loop:
            asyncio.run_coroutine_threadsafe(
                self.sendHook(self.parent, f"ASKFRIEND {user}"),
                self.parent.loop
            )
        self.destroy()


class ConnectionPopup(ctk.CTkToplevel):
    """Popup pour saisir l'adresse du serveur"""
    def __init__(self, parent, master, sendHook=None, default_ip="leovelazquez.fr", default_port="484"):
        super().__init__(master)
        self.sendHook = sendHook
        self.parent = parent
        self.title("Connexion réseau")
        self.geometry("320x220")
        self.resizable(False, False)

        ctk.CTkLabel(self, text="Adresse du serveur", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 6))
        
        self.ip_entry = ctk.CTkEntry(self, placeholder_text="IP")
        self.ip_entry.pack(pady=6, padx=20)
        self.ip_entry.insert(0, default_ip)

        ctk.CTkLabel(self, text="Port", font=ctk.CTkFont(size=14)).pack(pady=(6, 2))
        
        self.port_entry = ctk.CTkEntry(self, placeholder_text="Port")
        self.port_entry.pack(pady=6, padx=20)
        self.port_entry.insert(0, default_port)

        frame_btn = ctk.CTkFrame(self, fg_color="transparent")
        frame_btn.pack(pady=12)

        ctk.CTkButton(frame_btn, text="Se connecter", width=110, command=self._connect).pack(side="left", padx=8)
        ctk.CTkButton(frame_btn, text="Annuler", width=90, fg_color="#b22222",
                     hover_color="#8b0000", command=self.destroy).pack(side="right", padx=8)

        self.ip_entry.focus()

    def _connect(self):
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        
        if not ip or not port:
            messagebox.showwarning("Erreur", "Merci de remplir l'adresse IP et le port")
            return
            
        try:
            port_int = int(port)
        except Exception:
            messagebox.showwarning("Erreur", "Le port doit être un nombre entier")
            return

        self.parent.server_ip = ip
        self.parent.server_port = port_int
        self.destroy()


async def async_mainloop(root, interval=0.01):
    """Boucle principale asynchrone pour Tkinter"""
    try:
        while True:
            root.update()
            await asyncio.sleep(interval)
    except Exception as e:
        print(f"Erreur dans la boucle: {e}")


# Exemple d'utilisation
async def sendHook(gui, text):
    """Hook d'exemple pour les tests"""
    if text.startswith("/login"):
        gui.set_username(text.split(" ")[1])
    await asyncio.sleep(0.1)


async def main():
    """Fonction principale pour les tests"""
    root = ctk.CTk()
    gui = ChatGUI(root, sendHook=sendHook)
    gui.loop = asyncio.get_event_loop()
    
    # Exemples
    gui.add_channel("général")
    gui.add_channel("dev")
    gui.add_friend("Alice")
    gui.add_friend("Bob")
    
    await async_mainloop(root)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication fermée")