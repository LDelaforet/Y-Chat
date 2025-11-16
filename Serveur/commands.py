import dbControl


# ========== Fonctions utilitaires ========== #

def send_success(user):
    """Envoie un message de succès au client."""
    user.send("SUCCESS")


def send_error(user, message):
    """Envoie un message d'erreur et déconnecte le client."""
    user.send(f"ERROR {message}")
    user.disconnect()


def send_warning(user, message):
    """Envoie un avertissement au client."""
    user.send(f"WARNING {message}")


def wrong_command(user):
    """Gère les commandes inconnues."""
    send_warning(user, "Commande inconnue")


def broadcast_to_users(userList, message, excludeUserId=None):
    """Envoie un message à tous les utilisateurs actifs."""
    for user in userList:
        try:
            if excludeUserId and user.id == excludeUserId:
                continue
            user.send(message)
        except:
            pass


# ========== Commandes de base ========== #

def help_command(user, commandList):
    """Affiche la liste des commandes disponibles."""
    for name, command in commandList.items():
        if name == "wrong_command":
            continue
        user.send(f"COMMAND {name}: {command['argsCount']} arguments attendus.")


def quit_command(user):
    """Déconnecte l'utilisateur."""
    user.disconnect()


def ping_command(user):
    """Répond au ping du client."""
    user.send("PONG")


def pong_command(user):
    """Traite la réponse PONG du client."""
    if user.pingSended:
        user.toggle_ping_sended()
        send_success(user)


# ========== Authentification ========== #

def user_command(user, username):
    """Définit le nom d'utilisateur temporaire."""
    if " " in username:
        send_warning(user, "Espaces non autorises en nom d'utilisateur")
        return
    user.tempUser = username
    send_success(user)


def pass_command(user, password):
    """Définit le mot de passe temporaire."""
    if " " in password:
        send_warning(user, "Espaces non autorises en mot de passe")
        return
    user.tempPasswd = password
    send_success(user)


def login_command(user):
    """Connecte l'utilisateur avec ses credentials."""
    if user.tempUser == "SERVER":
        send_warning(user, "Connection a SERVER impossible")
        return

    if not user.tempUser or not user.tempPasswd:
        send_warning(user, "Nom d'utilisateur / mot de passe vide")
        return
    
    userId = dbControl.connect(user.tempUser, user.tempPasswd)
    if userId is None:
        send_warning(user, "Impossible de se connecter")
        return
    
    user.id = userId
    user.username = user.tempUser
    user.tempUser = ""
    user.tempPasswd = ""
    user.send(f"LOGGED {user.username}")
    print("Connexion de l'utilisateur",user.username)


def register_command(user):
    """Enregistre un nouvel utilisateur."""
    if not user.tempUser or not user.tempPasswd:
        send_warning(user, "Nom d'utilisateur / mot de passe vide")
        return
    
    if dbControl.get_user_id_by_username(user.tempUser) is not None:
        send_warning(user, "Nom d'utilisateur deja utilise")
        return
    
    dbControl.register(user.tempUser, user.tempPasswd)
    send_success(user)


def password_edit_command(user, newPassword):
    """Modifie le mot de passe de l'utilisateur."""
    dbControl.change_password(user.id, newPassword)
    send_success(user)


# ========== Gestion des utilisateurs ========== #

def get_id_command(user):
    """Récupère l'ID de l'utilisateur connecté."""
    if user.id is not None:
        user.send(f"USERID {user.username} {user.id}")
    else:
        send_warning(user, "Impossible de recuperer votre id")


def get_user_id_command(user, username):
    """Récupère l'ID d'un utilisateur par son nom."""
    userId = dbControl.get_user_id_by_username(username)
    if userId is not None:
        user.send(f"USERID {username} {userId}")
    else:
        send_warning(user, f"L'utilisateur {username} n'existe pas.")


def username_command(user, userId):
    """Récupère le nom d'utilisateur par son ID."""
    try:
        userId = int(userId)
    except:
        send_warning(user, "Veuillez entrer un chiffre en Id")
        return

    username = dbControl.get_username_by_user_id(userId)
    if username is None:
        send_warning(user, "Impossible de trouver l'utilisateur")
    else:
        user.send(f"USERID {username} {userId}")


# ========== Gestion des amitiés ========== #

def ask_friend_command(userList, user, username):
    """Envoie ou accepte une demande d'ami."""
    userId = user.id
    friendId = dbControl.get_user_id_by_username(username)

    if userId == friendId:
        send_warning(user, "Vous ne pouvez pas vous demander en ami")
        return
    
    if userId is None:
        send_warning(user, "Impossible de récuperer votre identifiant")
        return
    
    if friendId is None:
        send_warning(user, f"Impossible de récuperer l'identifiant de l'utilisateur {username}")
        return

    friendshipId = dbControl.get_friendship_id_by_ids(userId, friendId)
    if not friendshipId:
        friendshipId = dbControl.get_friendship_id_by_ids(friendId, userId)

    if friendshipId is None:
        dbControl.make_friend_request(userId, friendId)
        send_success(user)
        user.send(f"YOUASKED {username}")
        broadcast_to_users(
            [u for u in userList if u.id == friendId],
            f"ASKEDYOU {user.username}"
        )
    else:
        if dbControl.is_friendship_pending(friendshipId):
            if dbControl.who_asked_friendship(userId, friendId) == friendId:
                privChanId = dbControl.new_channel(f"PRIVATE-{userId}-{friendId}", True)
                dbControl.accept_friendship(friendshipId, privChanId)
                send_success(user)
                user.send(f"FRIEND {username}")
                broadcast_to_users(
                    [u for u in userList if u.id == friendId],
                    f"FRIEND {user.username}"
                )
            else:
                send_warning(user, "Vous avez deja demande cette personne en ami")
        else:
            send_warning(user, "Cette personne est deja votre ami")


def reject_friend_command(user, username):
    """Refuse une demande d'ami."""
    userId = user.id
    friendId = dbControl.get_user_id_by_username(username)

    if userId == friendId:
        send_warning(user, "Vous ne pouvez pas vous demander en ami")
        return

    if userId is None:
        send_warning(user, "Impossible de récuperer votre identifiant")
        return
    
    if friendId is None:
        send_warning(user, f"Impossible de récuperer l'identifiant de l'utilisateur {username}")
        return

    friendshipId = dbControl.get_friendship_id_by_ids(userId, friendId)
    if not friendshipId:
        friendshipId = dbControl.get_friendship_id_by_ids(friendId, userId)

    if friendshipId is None:
        send_warning(user, "Aucune demande d'ami n'a été envoyée")
    else:
        privChannelId = dbControl.get_private_channel_id_by_friendship_id(friendshipId)
        if privChannelId is not None:
            dbControl.remove_channel(privChannelId)
        dbControl.refuse_friendship(friendshipId)


def friend_list_command(user):
    """Liste tous les amis de l'utilisateur."""
    userId = user.id
    if userId is None:
        send_warning(user, "Impossible de récuperer votre identifiant")
        return

    friendships = dbControl.list_friendships_ids(userId)
    if not friendships:
        return

    for friendshipId in friendships:
        if dbControl.is_friendship_pending(friendshipId):
            continue
        
        friendshipIds = dbControl.get_user_id_by_friendship(friendshipId)
        if not friendshipIds:
            continue
        
        try:
            friendId = friendshipIds[1] if friendshipIds[0] == userId else friendshipIds[0]
            friendUsername = dbControl.get_username_by_user_id(friendId)
            user.send(f"FRIEND {friendUsername}")
        except Exception:
            continue


def friend_asked_command(user):
    """Liste les demandes d'ami envoyées."""
    userId = user.id
    askedList = dbControl.list_friendships_ids(userId)
    if not askedList:
        return
    
    for friendshipId in askedList:
        if dbControl.is_friendship_pending(friendshipId):
            friendshipIds = dbControl.get_user_id_by_friendship(friendshipId)
            if friendshipIds[0] != userId:
                continue
            friendName = dbControl.get_username_by_user_id(friendshipIds[1])
            user.send(f"YOUASKED {friendName}")


def asked_friend_command(user):
    """Liste les demandes d'ami reçues."""
    userId = user.id
    askedList = dbControl.list_friendships_ids(userId)
    if not askedList:
        return
    
    for friendshipId in askedList:
        if dbControl.is_friendship_pending(friendshipId):
            friendshipIds = dbControl.get_user_id_by_friendship(friendshipId)
            if friendshipIds[1] != userId:
                continue
            friendName = dbControl.get_username_by_user_id(friendshipIds[0])
            user.send(f"ASKEDYOU {friendName}")


# ========== Gestion des channels ========== #

def channel_list_command(user):
    """Liste tous les channels publics."""
    if dbControl.check_mod_by_username(user.username):
        user.send("CHANNEL commands")
    
    for channelInfo in dbControl.get_channel_list():
        channelId, channelName, isPrivate = channelInfo
        if channelName == "commands":
            continue
        if isPrivate == 0:
            user.send(f"CHANNEL {channelName}")


# ========== Gestion des messages ========== #

def new_msg_command(userList, user, channel, content):
    """Envoie un message dans un channel."""
    userId = user.id

    if channel == "commands" and not dbControl.check_mod_by_username(user.username):
        send_warning(user, "Vous n'avez pas les permissions requises")
        return
    
    channelId = dbControl.get_channel_id_by_name(channel)
    if userId is None:
        send_warning(user, "Vous n'etes pas connecte")
        return
    
    messageId = dbControl.send_message(userId, channelId, content)
    username = user.username
    msgInfo = dbControl.get_message_info(messageId)
    
    if msgInfo and len(msgInfo) >= 4:
        timestamp = msgInfo[2].replace(" ", "_")
        message = " ".join(["MSG", channel, username, timestamp, content])
        broadcast_to_users(userList, message, excludeUserId=userId)
    
    if channel == "commands":
        admin_command_runner(userList, content)


def list_msg_command(user, channel, offset):
    """Liste les messages d'un channel."""
    try:
        offset = int(offset)
    except:
        send_warning(user, "Offset doit etre un int")
        return
    
    channelId = dbControl.get_channel_id_by_name(channel)
    if channelId is None:
        send_warning(user, f"Le channel {channel} est introuvable")
        return

    msgList = dbControl.read_messages(channelId, offset)
    for row in msgList:
        messageId = row[0] if isinstance(row, (list, tuple)) else row
        msgInfo = dbControl.get_message_info(messageId)
        if not msgInfo or len(msgInfo) < 4:
            continue
        
        senderName = dbControl.get_username_by_user_id(msgInfo[1])
        timestamp = msgInfo[2].replace(" ", "_")
        content = msgInfo[3]
        user.send(" ".join(["MSG", channel, senderName, timestamp, content]))


def new_priv_msg_command(userList, user, username, content):
    """Envoie un message privé à un ami."""
    userId = user.id
    if userId is None:
        send_warning(user, "Vous n'etes pas connecte")
        return
    
    friendId = dbControl.get_user_id_by_username(username)
    if friendId is None:
        send_warning(user, "Utilisateur introuvable")
        return
    
    friendshipId = dbControl.get_friendship_id_by_ids(userId, friendId)
    if friendshipId is None:
        friendshipId = dbControl.get_friendship_id_by_ids(friendId, userId)

    if friendshipId is None:
        send_warning(user, "Vous n'etes pas ami avec l'utilisateur")
        return
    
    privateChannelId = dbControl.get_private_channel_id_by_friendship_id(friendshipId)
    if privateChannelId is None:
        send_warning(user, "Impossible de trouver le canal prive")
        return
    
    messageId = dbControl.send_message(userId, privateChannelId, content)
    send_success(user)
    
    msgInfo = dbControl.get_message_info(messageId)
    if msgInfo and len(msgInfo) >= 4:
        timestamp = msgInfo[2].replace(" ", "_")
        message = " ".join(["PRIVMSG", username, user.username, timestamp, content])
        broadcast_to_users(
            [u for u in userList if u.id == friendId],
            message
        )


def list_priv_msg_command(user, username, offset):
    """Liste les messages privés avec un ami."""
    userId = user.id
    if userId is None:
        send_warning(user, "Vous n'etes pas connecte")
        return
    
    friendId = dbControl.get_user_id_by_username(username)
    if friendId is None:
        send_warning(user, "Utilisateur introuvable")
        return
    
    friendshipId = dbControl.get_friendship_id_by_ids(userId, friendId)
    if friendshipId is None:
        friendshipId = dbControl.get_friendship_id_by_ids(friendId, userId)

    try:
        offset = int(offset)
    except:
        send_warning(user, "Offset doit etre un int")
        return

    channelId = dbControl.get_private_channel_id_by_friendship_id(friendshipId)
    if channelId is None:
        send_warning(user, f"Le channel prive associe a {username} est introuvable")
        return

    msgList = dbControl.read_messages(channelId, offset)
    for row in msgList:
        messageId = row[0] if isinstance(row, (list, tuple)) else row
        msgInfo = dbControl.get_message_info(messageId)
        if not msgInfo or len(msgInfo) < 4:
            continue
        
        sender = dbControl.get_username_by_user_id(msgInfo[1])
        timestamp = msgInfo[2].replace(" ", "_")
        content = msgInfo[3]
        user.send(f"PRIVMSG {username} {sender} {timestamp} {content}")


# ========== Commandes modérateur ========== #

def new_chan_command(chanName):
    """Crée un nouveau channel."""
    if dbControl.get_channel_id_by_name(chanName) is not None:
        dbControl.send_message(0, 0, "ERREUR: Le channel existe deja")
        return
    dbControl.new_channel(chanName)
    dbControl.send_message(0, 0, "Channel crée")


def ren_chan_command(oldChanName, newChanName):
    """Renomme un channel."""
    if oldChanName == "commands":
        dbControl.send_message(0, 0, "ERREUR: Impossible de renommer commands")
        return
    
    chanId = dbControl.get_channel_id_by_name(oldChanName)
    if chanId is None:
        dbControl.send_message(0, 0, "ERREUR: Le channel n'existe pas")
        return
    
    dbControl.rename_channel(chanId, newChanName)
    dbControl.send_message(0, 0, "Channel renommé")


def del_chan_command(chanName):
    """Supprime un channel."""
    if chanName == "commands":
        dbControl.send_message(0, 0, "ERREUR: Impossible de supprimer commands")
        return
    
    chanId = dbControl.get_channel_id_by_name(chanName)
    if chanId is None:
        dbControl.send_message(0, 0, "ERREUR: Le channel n'existe pas")
        return
    
    dbControl.remove_channel(chanId)
    dbControl.send_message(0, 0, "Channel supprimé")


def wipe_chan_command(chanName):
    """Vide tous les messages d'un channel."""
    chanId = dbControl.get_channel_id_by_name(chanName)
    if chanId is None:
        dbControl.send_message(0, 0, "ERREUR: Le channel n'existe pas")
        return
    
    dbControl.wipe_channel(chanId)
    dbControl.send_message(0, 0, "Channel vidé")


def admin_command_runner(userList, message):
    """Exécute une commande admin depuis le channel commands."""
    messageCommandList = {
        "NEWCHAN": {
            "function": new_chan_command,
            "argsCount": 1
        },
        "RENCHAN": {
            "function": ren_chan_command,
            "argsCount": 2
        },
        "DELCHAN": {
            "function": del_chan_command,
            "argsCount": 1
        },
        "WIPECHAN": {
            "function": wipe_chan_command,
            "argsCount": 1
        }
    }
    
    parts = message.split(" ")
    command = parts[0].upper()
    args = parts[1:]
    
    if command not in messageCommandList:
        dbControl.send_message(0, 0, "Commande inconnue")
        return
    
    commandInfo = messageCommandList[command]
    if len(args) != commandInfo["argsCount"]:
        dbControl.send_message(0, 0, "Nombre d'arguments invalide")
        return
    
    commandInfo["function"](*args)
    broadcast_to_users(userList, "CHANUPDATE")


# ========== Dictionnaire des commandes ========== #

COMMAND_LIST = {
    "HELP": {
        "function": help_command,
        "argsCount": 0
    },
    "QUIT": {
        "function": quit_command,
        "argsCount": 0
    },
    "PING": {
        "function": ping_command,
        "argsCount": 0
    },
    "PONG": {
        "function": pong_command,
        "argsCount": 0
    },
    "USER": {
        "function": user_command,
        "argsCount": 1
    },
    "PASS": {
        "function": pass_command,
        "argsCount": 1
    },
    "LOGIN": {
        "function": login_command,
        "argsCount": 0
    },
    "REGISTER": {
        "function": register_command,
        "argsCount": 0
    },
    "PASSWORDEDIT": {
        "function": password_edit_command,
        "argsCount": 1
    },
    "GETID": {
        "function": get_id_command,
        "argsCount": 0
    },
    "GETUSERID": {
        "function": get_user_id_command,
        "argsCount": 1
    },
    "USERNAME": {
        "function": username_command,
        "argsCount": 1
    },
    "ASKFRIEND": {
        "function": ask_friend_command,
        "argsCount": 1,
        "needUserList": True
    },
    "ACCEPTFRIEND": {
        "function": ask_friend_command,
        "argsCount": 1,
        "needUserList": True
    },
    "REJECTFRIEND": {
        "function": reject_friend_command,
        "argsCount": 1
    },
    "FRIENDLIST": {
        "function": friend_list_command,
        "argsCount": 0
    },
    "FRIENDASKED": {
        "function": friend_asked_command,
        "argsCount": 0
    },
    "ASKEDFRIEND": {
        "function": asked_friend_command,
        "argsCount": 0
    },
    "CHANNELLIST": {
        "function": channel_list_command,
        "argsCount": 0
    },
    "NEWMSG": {
        "function": new_msg_command,
        "argsCount": 2,
        "needUserList": True
    },
    "LISTMSG": {
        "function": list_msg_command,
        "argsCount": 2
    },
    "NEWPRIVMSG": {
        "function": new_priv_msg_command,
        "argsCount": 2,
        "needUserList": True
    },
    "LISTPRIVMSG": {
        "function": list_priv_msg_command,
        "argsCount": 2
    },
    "wrong_command": {
        "function": wrong_command,
        "argsCount": 0
    }
}