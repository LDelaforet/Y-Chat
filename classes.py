import socket

class User():
    def __init__(self, socket):
        self.socket = socket
        self.isActive = True
        self.tempUser = ""
        self.tempPasswd = ""
        self.id = None
        self.username = "NONE"
        self.pingSended = False
        pass

    def disconnect(self):
        # Mark inactive and close socket safely; log for debugging
        self.isActive = False
        try:
            peer = None
            try:
                peer = self.socket.getpeername()
            except Exception:
                pass
            print(f"Disconnecting user {self.username} socket={peer}")
            self.socket.close()
        except Exception as e:
            print("Erreur lors de la deconnexion du socket:", e)
    
    def toggle_pingSended(self):
        self.pingSended = not self.pingSended
    
    def is_pingSended(self):
        return self.pingSended

    def set_username(self, username):
        self.username = username
    
    def set_id(self, id):
        self.id = id
    
    def set_tempUser(self, tempUser):
        self.tempUser = tempUser

    def set_tempPasswd(self, tempPasswd):
        self.tempPasswd = tempPasswd
    
    def send(self, message):
        try:
            # Ensure each message is terminated so client can split by lines
            self.socket.sendall((message + "\r\n").encode())
        except Exception:
            # If sending fails, consider the user disconnected
            try:
                self.socket.close()
            except:
                pass
    

    def get_username(self):
        return(self.username)
    
    def get_id(self):
        return(self.id)
    
    def get_tempUser(self):
        return(self.tempUser)

    def get_tempPasswd(self):
        return(self.tempPasswd)