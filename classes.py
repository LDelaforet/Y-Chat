import socket

class User():
    def __init__(self, socket):
        self.socket = socket
        self.isActive = True
        self.tempUser = ""
        self.tempPasswd = ""
        self.id = None
        self.username = ""
        pass

    def desactivate(self):
        self.isActive = False
        self.socket.close()
    
    def check_if_alive(self):
        pass

    def set_username(self, username):
        self.username = username
    
    def set_id(self, id):
        self.id = id
    
    def set_tempUser(self, tempUser):
        self.tempUser = tempUser

    def set_tempPasswd(self, tempPasswd):
        self.tempPasswd = tempPasswd
    

    

    def get_username(self):
        return(self.username)
    
    def get_id(self):
        return(self.id)
    
    def get_tempUser(self):
        return(self.tempUser)

    def get_tempPasswd(self):
        return(self.tempPasswd)