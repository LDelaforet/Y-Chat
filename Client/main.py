import socket
import asyncio
import threading
from GUI import ChatGUI as GUI, ctk
from commands import COMMAND_HANDLERS


# Socket globale
server_socket = None
# Buffers pour les réceptions partielles
receive_buffers = {}


async def send_hook(gui, message):
    """Hook appelé par la GUI pour envoyer des messages"""
    
    if message.upper().startswith("/LOGIN"):
        parts = message.split(" ")
        username = parts[1]
        password = parts[2]
        await send_message("USER " + username)
        await send_message("PASS " + password)
        await send_message("LOGIN")
    elif message.upper().startswith("/REGISTER"):
        parts = message.split(" ")
        username = parts[1]
        password = parts[2]
        await send_message("USER " + username)
        await send_message("PASS " + password)
        await send_message("REGISTER")
    else:
        await send_message(message)


async def send_message(text):
    """Envoie un message au serveur de manière asynchrone"""
    global server_socket
    
    if not server_socket:
        return
    
    try:
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(server_socket, (text + "\r\n").encode())
        await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Erreur lors de l'envoi: {e}")


async def receive_loop(sock, gui):
    """Boucle de réception asynchrone des messages du serveur"""
    sock.setblocking(False)
    loop = asyncio.get_running_loop()
    
    try:
        while True:
            try:
                data = await loop.sock_recv(sock, 1024)
                if not data:
                    print("Déconnecté du serveur")
                    return
            except ConnectionAbortedError:
                print("Connexion interrompue")
                return
            except Exception as e:
                print(f"Erreur de réception: {e}")
                return
            
            # Décoder les données
            try:
                text = data.decode()
            except Exception as e:
                print(f"Erreur de décodage: {e}")
                continue
            
            # Accumuler dans le buffer et découper par lignes (CRLF)
            buffer = receive_buffers.get(id(sock), "") + text
            parts = buffer.split("\r\n")
            
            # Tous sauf le dernier sont des lignes complètes
            complete_lines = parts[:-1]
            # Le dernier élément est soit "" soit un fragment partiel
            receive_buffers[id(sock)] = parts[-1]
            
            # Traiter chaque ligne complète
            for line in complete_lines:
                if not line:
                    continue
                
                command = line.split(" ")
                run_command(sock, gui, command)
    
    except Exception as e:
        print(f"Erreur dans la boucle de réception: {e}")


def run_command(sock, gui, command):
    """
    Exécute une commande reçue du serveur.
    
    Args:
        sock: Socket du serveur
        gui: Instance de la GUI
        command: Liste [nom_commande, arg1, arg2, ...]
    """
    if not command:
        return
    
    command_name = command[0].upper()
    
    if command_name not in COMMAND_HANDLERS:
        print(f"Commande non reconnue: {command_name}")
        return
    
    handler, expected_args = COMMAND_HANDLERS[command_name]
    
    # Gérer le cas où le dernier argument peut contenir des espaces
    # (on regroupe tous les arguments excédentaires dans le dernier)
    if len(command) - 1 > expected_args:
        args = command[1:expected_args]
        last_arg = " ".join(command[expected_args:])
        args.append(last_arg)
    else:
        args = command[1:expected_args + 1]
    
    # Exécuter dans le thread GUI en utilisant call_soon_threadsafe
    try:
        if hasattr(gui, 'event_queue') and gui.event_queue is not None:
            gui.event_queue.put((handler, sock, args))
        else:
            gui.master.after(0, lambda: handler(sock, gui, *args))
    except Exception as e:
        print(f"Erreur lors de l'exécution de {command_name}: {e}")


def start_async_loop(loop):
    """Démarre la boucle asyncio dans un thread séparé"""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main():
    global server_socket
    
    # Créer la GUI
    root = ctk.CTk()
    gui = GUI(root, sendHook=send_hook, show_login_at_start=False)
    
    # Demander l'adresse du serveur
    try:
        gui.show_connection_sync()
    except Exception as e:
        print(f"Erreur lors de l'affichage de la popup de connexion: {e}")
    
    # Vérifier que les informations ont été fournies
    server_ip = getattr(gui, 'server_ip', None)
    server_port = getattr(gui, 'server_port', None)
    
    if not server_ip or not server_port:
        print("Aucune adresse serveur fournie. Arrêt.")
        return
    
    # Résoudre l'adresse IP
    try:
        server_ip = socket.gethostbyname(server_ip)
    except Exception as e:
        print(f"Erreur lors de la résolution DNS: {e}")
        return
    
    # Créer la socket et la boucle asyncio
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    gui.loop = loop
    
    # Connexion au serveur
    try:
        loop.run_until_complete(loop.sock_connect(sock, (server_ip, int(server_port))))
        print(f"Connecté au serveur {server_ip}:{server_port}")
        # Assigner à la variable globale APRÈS la connexion réussie
        server_socket = sock
    except Exception as e:
        print(f"Connexion échouée: {e}")
        return
    
    # Afficher la popup de login après connexion réussie
    try:
        gui.master.after(0, lambda: gui.show_login_sync())
    except Exception as e:
        print(f"Impossible d'afficher la popup de login: {e}")
    
    # Lancer la boucle de réception
    loop.create_task(receive_loop(server_socket, gui))
    
    # Démarrer la boucle asyncio dans un thread séparé
    thread = threading.Thread(target=start_async_loop, args=(loop,), daemon=True)
    thread.start()
    
    # Démarrer la boucle Tkinter
    root.mainloop()
    
    # Nettoyage à la fermeture
    if server_socket:
        try:
            server_socket.close()
        except Exception:
            pass
    
    loop.call_soon_threadsafe(loop.stop)


if __name__ == "__main__":
    main() 