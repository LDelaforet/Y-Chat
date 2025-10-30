import socket
import asyncio
import dbControl
from classes import *

def admin_command_runner(message):
    # Jsp ou le mettre....
    messageCommandList = {
        "NEWCHAN": {
            "function": NEWCHAN,
            "argsCount": 1
        },
        "RENCHAN": {
            "function": RENCHAN,
            "argsCount": 2
        },
        "DELCHAN": {
            "function": DELCHAN,
            "argsCount": 1
        },
        "WIPECHAN": {
            "function": WIPECHAN,
            "argsCount": 1
        }
    }
    command = message.split(" ")[0].upper()
    args = message.split(" ")[1:]
    if command in messageCommandList:
        command = messageCommandList[command]
    else:
        dbControl.send_message(0, 0, "Commande inconnue")
        return
    
    if len(args) != command["argsCount"]:
        dbControl.send_message(0, 0, "Nombre d'arguments invalide")
        return

    command["function"](*args)


def send_SUCCESS(user):
    user.socket.send("SUCCESS".encode())

def send_ERROR(user, message):
    user.socket.send(("ERROR " + message).encode())
    user.desactivate()

def send_WARNING(user, message):
    user.socket.send(("WARNING " + message).encode())

def wrong_command(user):
    send_WARNING(user, "Commande inconnue")

def HELP(user, commandList):
    for name, x in commandList.items():
        if name == "wrong_command":
            continue
        user.socket.send((name + ": " + str(x["argsCount"]) + " arguments attendus.\n").encode())

def QUIT(user):
    user.desactivate()

def PING(user):
    user.socket.send("PONG".encode())

def USER(user, username):
    if " " in username:
        send_WARNING(user, "Espaces non autorises en nom d'utilisateur")
        return
    user.set_tempUser(username)
    send_SUCCESS(user)

def PASS(user, password):
    if " " in password:
        send_WARNING(user, "Espaces non autorises en mot de passe")
        return
    user.set_tempPasswd(password)
    send_SUCCESS(user)

def LOGIN(user):
    if user.get_tempUser() == "SERVER":
        send_WARNING(user, "Connection a SERVER impossible")
        return

    if user.get_tempUser() == "" or user.get_tempUser() == "":
        send_WARNING(user, "Nom d'utilisateur / mot de passe vide")
        return
    userID = dbControl.connect(user.get_tempUser(), user.get_tempPasswd())
    if userID == None:
        send_WARNING(user, "Impossible de se connecter")
        return
    else:
        user.set_id(userID)
        user.set_username(user.get_tempUser())

        user.set_tempUser("")
        user.set_tempPasswd("")
        send_SUCCESS(user)

def REGISTER(user):
    if user.get_tempUser() == "" or user.get_tempUser() == "":
        send_WARNING(user, "Nom d'utilisateur / mot de passe vide")
        return
    print("get_ID: " + str(dbControl.get_user_id_by_username(user.get_tempUser())))
    if dbControl.get_user_id_by_username(user.get_tempUser()) != None:
        send_WARNING(user, "Nom d'utilisateur deja utilise")
        return
    dbControl.register(user.get_tempUser(), user.get_tempPasswd())
    send_SUCCESS(user)

def GETID(user):
    if user.get_id != None:
        print(user.get_username())
        print(user.get_id())
        user.socket.send(("USERID " + user.get_username() + " " + str(user.get_id())).encode())
    else:
        send_WARNING(user, "Impossible de recuperer votre id")

def GETUSERID(user, utilisateur):
    userId = dbControl.get_user_id_by_username(utilisateur)
    if userId != None:
        user.socket.send(("USERID " + utilisateur + " " + str(userId)).encode())
    else:
        send_WARNING(user, "Impossible de recuperer l'id de l'utilisateur: " + utilisateur)

def ASKFRIEND(user, utilisateur):
    userId = user.get_id()
    friendId = dbControl.get_user_id_by_username(utilisateur)

    print("\n",user.get_username(),"("+str(userId)+") demande ",utilisateur,"("+str(friendId)+") en ami")

    if userId == friendId:
        send_WARNING(user, "Vous ne pouvez pas vous demander en ami")
        return
    
    if userId == None:
        send_WARNING(user, "Impossible de récuperer votre identifiant")
        return
    if friendId == None:
        send_WARNING(user, "Impossible de récuperer l'identifiant de l'utilisateur " + utilisateur)
        return

    friendshipId = dbControl.get_friendship_id_by_ids(userId, friendId)
    
    if not friendshipId:
        friendshipId = dbControl.get_friendship_id_by_ids(friendId, userId)
    
    print("l'id de friendship est:",friendshipId)

    if friendshipId == None:
        print("l'id est nul, on crée la requete")
        dbControl.make_friend_request(userId, friendId)
        send_SUCCESS(user)
    else:
        if dbControl.is_friendship_pending(friendshipId):
            print(user.get_username(),"a deja fait une demande d'ami")
            if dbControl.who_asked_friendship(userId, friendId) == friendId:
                print(utilisateur,"a deja fait une demande d'ami, on accepte")
                privChanId = dbControl.new_channel("PRIVATE-" + str(userId) + "-" + str(friendId), True)
                print("Le channel privé a pour id: "+ str(privChanId))
                dbControl.accept_friendship(friendshipId, privChanId)
                send_SUCCESS(user)
            else:
                send_WARNING(user, "Vous avez deja demande cette personne en ami")
        else:
            send_WARNING(user, "Cette personne est deja votre ami")

def REJECTFRIEND(user, utilisateur):
    userId = user.get_id()
    friendId = dbControl.get_user_id_by_username(utilisateur)

    if userId == friendId:
        send_WARNING(user, "Vous ne pouvez pas vous demander en ami")
        return

    if userId == None:
        send_WARNING(user, "Impossible de récuperer votre identifiant")
        return
    if friendId == None:
        send_WARNING(user, "Impossible de récuperer l'identifiant de l'utilisateur " + utilisateur)
        return

    friendshipId = dbControl.get_friendship_id_by_ids(userId, friendId)
    
    if not friendshipId:
        friendshipId = dbControl.get_friendship_id_by_ids(friendId, userId)
    

    if friendshipId == None:
        send_WARNING(user, "Aucune demande d'ami n'a été envoyée")
    else:
        privChannelId = dbControl.get_private_channel_id_by_friendship_id(friendshipId)
        if privChannelId != None:
            dbControl.remove_channel(privChannelId)
        dbControl.refuse_friendship(friendshipId)

def FRIENDLIST(user):
    userId = user.get_id()
    for x in dbControl.list_friendships_ids(userId):
        friendship = dbControl.get_user_id_by_friendship(x)
        # C'est un ptn de monolithe, a opti
        user.socket.send(("FRIEND " + str(friendship[friendship.index(userId) - 1])).encode())

def USERNAME(user, userId):
    try:
        userId = int(userId)
    except:
        send_WARNING(user, "Veuillez entrer un chiffre en Id")

    username = dbControl.get_username_by_user_id(userId)
    if username == None:
        send_WARNING(user, "Impossible de trouver l'utilisateur")
    else:
        user.socket.send(("USERID " + username + " " + str(userId)).encode())

def NEWMSG(user, channel, content):
    userId = user.get_id()

    if channel == "commands" and (not dbControl.check_mod_by_username(user.get_username())):
        send_WARNING(user, "Vous n'avez pas les permissions requises")
        return
    
    channelId = dbControl.get_channel_id_by_name(channel)
    if userId == None:
        send_WARNING(user, "Vous n'etes pas connecte")
    dbControl.send_message(userId, channelId, content)
    send_SUCCESS(user)
    if channel == "commands": admin_command_runner(content)

def LISTMSG(user, channel, offset):
    try:
        offset = int(offset)
    except:
        send_WARNING(user, "Offset doit etre un int")
    
    channelId = dbControl.get_channel_id_by_name(channel)

    if channelId == None:
        send_WARNING(user, "Le channel " + channel + " est introuvable")

    msgList = dbControl.read_messages(channelId, offset)

    for x in msgList:
        username = dbControl.get_username_by_user_id(x[0])
        content = x[1]
        timestamp = x[2].replace(" ","_")
        user.socket.send(("MSG " + channel + " " + username + " " + timestamp + " " + content).encode())

def NEWPRIVMSG(user, username, message):
    userId = user.get_id()
    if userId == None:
        send_WARNING(user, "Vous n'etes pas connecte")
    
    friendId = dbControl.get_user_id_by_username(username)
    if friendId == None:
        send_WARNING(user, "Utilisateur introuvable")
        return
    friendshipId = dbControl.get_friendship_id_by_ids(userId, friendId)

    if friendshipId == None: friendshipId = dbControl.get_friendship_id_by_ids(friendId, userId)

    if friendshipId == None:
        send_WARNING(user, "Vous n'etes pas ami avec l'utilisateur")
        return
    privateChannelId = dbControl.get_private_channel_id_by_friendship_id(friendshipId)
    if privateChannelId == None:
        send_WARNING(user, "Impossible de trouver le canal prive")
        return
    
    dbControl.send_message(userId, privateChannelId, message)
    send_SUCCESS(user)

def LISTPRIVMSG(user, username, offset):
    userId = user.get_id()
    if userId == None:
        send_WARNING(user, "Vous n'etes pas connecte")
    
    friendId = dbControl.get_user_id_by_username(username)
    if friendId == None:
        send_WARNING(user, "Utilisateur introuvable")
        return
    friendshipId = dbControl.get_friendship_id_by_ids(userId, friendId)

    if friendshipId == None: friendshipId = dbControl.get_friendship_id_by_ids(friendId, userId)

    try:
        offset = int(offset)
    except:
        send_WARNING(user, "Offset doit etre un int")

    channelId = dbControl.get_private_channel_id_by_friendship_id(friendshipId)

    if channelId == None:
        send_WARNING(user, "Le channel prive associe a " + username + " est introuvable")

    msgList = dbControl.read_messages(channelId, offset)

    for x in msgList:
        sender = dbControl.get_username_by_user_id(x[0])
        content = x[1]
        timestamp = x[2].replace(" ","_")
        user.socket.send(("PRIVMSG " + username + " " + sender + " " + timestamp + " " + content).encode())

def CHANNELLIST(user):
    if dbControl.check_mod_by_username(user.get_username()):
        user.socket.send("CHANNEL commands".encode())
    isCommandChannel = False
    for x in dbControl.get_channel_list():
        if x[1] == "commands": continue
        if x[2] == 0:
            user.socket.send(("CHANNEL " + x[1]).encode())

# ---------- Commandes modérateur ---------- #

def NEWCHAN(chanName):
    if dbControl.get_channel_id(chanName) != None:
        dbControl.send_message(0, 0, "ERREUR: Le channel existe deja")
        return
    dbControl.new_channel(chanName)
    dbControl.send_message(0, 0, "Channel crée")

def RENCHAN(oldChanName, newChanName):
    if oldChanName == "commands":
        dbControl.send_message(0, 0, "ERREUR: Impossible de renommer commands")
        return
    
    chanId = dbControl.get_channel_id(oldChanName)
    if chanId == None:
        dbControl.send_message(0, 0, "ERREUR: Le channel n'existe pas")
        return
    
    dbControl.rename_channel(chanId, newChanName)
    dbControl.send_message(0, 0, "Channel renommé")

def DELCHAN(chanName):
    if chanName == "commands":
        dbControl.send_message(0, 0, "ERREUR: Impossible de supprimer commands")
        return
    
    chanId = dbControl.get_channel_id(chanName)
    if chanId == None:
        dbControl.send_message(0, 0, "ERREUR: Le channel n'existe pas")
        return
    
    dbControl.remove_channel(chanId)
    dbControl.send_message(0, 0, "Channel supprimé")

def WIPECHAN(chanName):
    chanId = dbControl.get_channel_id(chanName)
    if chanId == None:
        dbControl.send_message(0, 0, "ERREUR: Le channel n'existe pas")
        return
    
    dbControl.wipe_channel(chanId)
    dbControl.send_message(0, 0, "Channel vidé")

commandList = {
    "HELP": {
        "function": HELP,
        "argsCount": 0
    },
    "QUIT": {
        "function": QUIT,
        "argsCount": 0
    },
    "PING": {
        "function": PING,
        "argsCount": 0
    },
    "USER": {
        "function": USER,
        "argsCount": 1
    },
    "PASS": {
        "function": PASS,
        "argsCount": 1
    },
    "LOGIN": {
        "function": LOGIN,
        "argsCount": 0
    },
    "REGISTER": {
        "function": REGISTER,
        "argsCount": 0
    },
    "wrong_command": {
        "function": wrong_command,
        "argsCount": 0
    },
    "GETID": {
        "function": GETID,
        "argsCount": 0
    },
    "GETUSERID": {
        "function": GETUSERID,
        "argsCount": 1
    },
    "ASKFRIEND": {
        "function": ASKFRIEND,
        "argsCount": 1
    },
    # Oui en fait ca fait sensiblement la meme chose
    "ACCEPTFRIEND": {
        "function": ASKFRIEND,
        "argsCount": 1
    },
    "REJECTFRIEND": {
        "function": REJECTFRIEND,
        "argsCount": 1
    },
    "FRIENDLIST": {
        "function": FRIENDLIST,
        "argsCount": 0
    },
    "USERNAME": {
        "function": USERNAME,
        "argsCount": 1
    },
    "NEWMSG": {
        "function": NEWMSG,
        "argsCount": 2
    },
    "LISTMSG": {
        "function": LISTMSG,
        "argsCount": 2
    },
    "NEWPRIVMSG": {
        "function": NEWPRIVMSG,
        "argsCount": 2
    },
    "LISTPRIVMSG": {
        "function": LISTPRIVMSG,
        "argsCount": 2
    },
    "CHANNELLIST": {
        "function": CHANNELLIST,
        "argsCount": 0
    }
}








#PROCHAINE ETAPE: LE CLIENT !!!!!!!!