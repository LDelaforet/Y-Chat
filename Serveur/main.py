import socket
import asyncio
import traceback
import dbControl
from commands import COMMAND_LIST, send_warning
from classes import User

# ========== Variables globales ========== #

users = []
debug = False
SERVER_PORT = 484
PING_INTERVAL = 5
PING_TIMEOUT = 5


# ========== Fonctions utilitaires ========== #

def remove_user(user):
    """Retire un utilisateur de la liste des utilisateurs connectés."""
    try:
        if user in users:
            users.remove(user)
    except Exception:
        pass


def initialize_server():
    """Initialise les données serveur (channel commands et utilisateur SERVER)."""
    isCommandChannel = False
    for channelInfo in dbControl.get_channel_list():
        if channelInfo[1] == "commands":
            isCommandChannel = True
            break
    
    if not isCommandChannel:
        dbControl.new_channel("commands", False, 0)
    
    if dbControl.get_user_id_by_username("SERVER") is None:
        dbControl.register("SERVER", "SERVER", 0)


# ========== Gestion du ping ========== #

async def ping_sender(user):
    """Envoie régulièrement des pings au client pour vérifier la connexion."""
    try:
        while user.isActive:
            if debug:
                break
            
            await asyncio.sleep(PING_INTERVAL)
            
            if not user.pingSended:
                user.toggle_ping_sended()
            
            user.send("PING")
            await asyncio.sleep(PING_TIMEOUT)
            
            if user.pingSended:
                user.disconnect()
                await asyncio.sleep(1)
                remove_user(user)
    except:
        return


# ========== Réception et traitement des commandes ========== #

async def command_receiver(user):
    """Reçoit et traite les commandes du client."""
    try:
        while user.isActive:
            try:
                received = await asyncio.get_running_loop().sock_recv(user.socket, 1024)
                if not received:
                    return
            except ConnectionAbortedError:
                return
            
            command = received.decode().replace("\r\n", "").split(" ")
            command_runner(user, command)
    except:
        return


def command_runner(user, command):
    """Exécute une commande reçue du client."""
    global debug
    
    if not command:
        return
    
    # Commandes spéciales de debug
    if command[0].upper() == "EXIT":
        exit()
    
    if command[0].upper() == "DEBUG":
        debug = True
        return
    
    if command[0].upper() == "HELP":
        COMMAND_LIST["HELP"]["function"](user, COMMAND_LIST)
        return
    
    if debug:
        print(command)
    
    # Récupération de la commande
    usedCommand = COMMAND_LIST.get(command[0].upper())
    if usedCommand is None:
        COMMAND_LIST["wrong_command"]["function"](user)
        return
    
    argsCount = usedCommand.get("argsCount", 0)
    
    # Reconstruction des arguments (pour gérer les espaces dans le dernier arg)
    if len(command) - 1 > argsCount:
        fixedArgs = command[1:argsCount]
        lastArg = " ".join(command[argsCount:])
        commandArgs = [user, *fixedArgs, lastArg]

    else:
        commandArgs = [user, *command[1:argsCount + 1]]
    
    # Vérification du nombre d'arguments
    if len(commandArgs) - 1 != argsCount:
        print(commandArgs)
        send_warning(user, "Nombre d'arguments incorrect")
        return
    
    # Ajout de la liste des utilisateurs si nécessaire
    if usedCommand.get("needUserList", False):
        commandArgs.insert(0, users)
    
    # Exécution de la commande
    if debug:
        usedCommand["function"](*commandArgs)
    else:
        try:
            usedCommand["function"](*commandArgs)
        except Exception as e:
            errorLine = traceback.format_exc()
            print(f"Erreur: {e}\n{errorLine}")
            send_warning(user, f"Erreur: {e}")


# ========== Acceptation des clients ========== #

async def client_accept(serverSocket):
    """Accepte les nouvelles connexions clients."""
    serverSocket.setblocking(False)
    loop = asyncio.get_running_loop()
    
    while True:
        clientSocket, address = await loop.sock_accept(serverSocket)
        print(f"Connection reçue: {address}")
        
        clientSocket.setblocking(False)
        user = User(clientSocket)
        users.append(user)
        
        asyncio.create_task(command_receiver(user))
        asyncio.create_task(ping_sender(user))


# ========== Point d'entrée ========== #

def main():
    """Point d'entrée du serveur."""
    # Initialisation
    initialize_server()
    
    # Création du socket serveur
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(("0.0.0.0", SERVER_PORT))
    serverSocket.listen(5)
    
    print(f"Serveur démarré sur le port {SERVER_PORT}")
    print("En attente de connections...")
    
    # Lancement de la boucle asyncio
    asyncio.run(client_accept(serverSocket))


if __name__ == "__main__":
    main()