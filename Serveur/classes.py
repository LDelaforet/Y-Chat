class User:
    """Représente un utilisateur connecté au serveur."""
    
    def __init__(self, socket):
        self.socket = socket
        self.isActive = True
        self.tempUser = ""
        self.tempPasswd = ""
        self.id = None
        self.username = "NONE"
        self.pingSended = False
    
    def disconnect(self):
        """Déconnecte l'utilisateur et ferme le socket proprement."""
        self.isActive = False
        try:
            peer = None
            try:
                peer = self.socket.getpeername()
            except Exception:
                pass
            
            self.socket.close()
        except Exception as e:
            pass
    
    def toggle_ping_sended(self):
        """Inverse l'état du ping envoyé."""
        self.pingSended = not self.pingSended
    
    def send(self, message):
        """Envoie un message au client via le socket."""
        try:
            self.socket.sendall((message + "\r\n").encode())
        except Exception:
            try:
                self.socket.close()
            except:
                pass