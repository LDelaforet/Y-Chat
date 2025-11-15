import socket
import asyncio
import time

import dbControl
from classes import *

def admin_command_runner(userList, message):
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

    for x in userList:
        try:
            x.send("CHANUPDATE")
        except:
            pass


def send_SUCCESS(user):
    user.send("SUCCESS")

def send_ERROR(user, message):
    user.send(("ERROR " + message))
    user.disconnect()

def send_WARNING(user, message):
    user.send(("WARNING " + message))

def wrong_command(user):
    send_WARNING(user, "Commande inconnue")

def HELP(user, commandList):
    for name, x in commandList.items():
        if name == "wrong_command":
            continue
        user.send(("COMMAND " + name + ": " + str(x["argsCount"]) + " arguments attendus."))

def QUIT(user):
    user.disconnect()

def PING(user):
    user.send("PONG")

def PONG(user):
    if user.is_pingSended():
        user.toggle_pingSended()
        send_SUCCESS(user)

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
        user.send("LOGGED " + user.get_username())

def REGISTER(user):
    if user.get_tempUser() == "" or user.get_tempUser() == "":
        send_WARNING(user, "Nom d'utilisateur / mot de passe vide")
        return
    if dbControl.get_user_id_by_username(user.get_tempUser()) != None:
        send_WARNING(user, "Nom d'utilisateur deja utilise")
        return
    dbControl.register(user.get_tempUser(), user.get_tempPasswd())
    send_SUCCESS(user)

def GETID(user):
    if user.get_id != None:
        user.send(("USERID " + user.get_username() + " " + str(user.get_id())))
    else:
        send_WARNING(user, "Impossible de recuperer votre id")

def GETUSERID(user, utilisateur):
    userId = dbControl.get_user_id_by_username(utilisateur)
    if userId != None:
        user.send(("USERID " + utilisateur + " " + str(userId)))
    else:
        send_WARNING(user, "Impossible de recuperer l'id de l'utilisateur: " + utilisateur)

def ASKFRIEND(userList, user, utilisateur):
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
        dbControl.make_friend_request(userId, friendId)
        send_SUCCESS(user)
        user.send("YOUASKED " + utilisateur)
        for x in userList:
            if x.get_id() == friendId:
                x.send("ASKEDYOU " + user.get_username())
    else:
        if dbControl.is_friendship_pending(friendshipId):
            if dbControl.who_asked_friendship(userId, friendId) == friendId:
                privChanId = dbControl.new_channel("PRIVATE-" + str(userId) + "-" + str(friendId), True)
                dbControl.accept_friendship(friendshipId, privChanId)
                send_SUCCESS(user)
                user.send("FRIEND " + utilisateur)
                for x in userList:
                    if x.get_id() == friendId:
                        x.send("FRIEND " + user.get_username())
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
    if userId == None:
        send_WARNING(user, "Impossible de récuperer votre identifiant")
        return

    friendships = dbControl.list_friendships_ids(userId)
    if friendships == None:
        return

    for friendship_id in friendships:
        if dbControl.is_friendship_pending(friendship_id):
            continue
        friendshipIds = dbControl.get_user_id_by_friendship(friendship_id)
        if not friendshipIds:
            continue
        try:
            if friendshipIds[0] == userId:
                friendId = friendshipIds[1]
            else:
                friendId = friendshipIds[0]
            friendUsername = dbControl.get_username_by_user_id(friendId)
            user.send(("FRIEND " + friendUsername))
        except Exception:
            continue


def USERNAME(user, userId):
    try:
        userId = int(userId)
    except:
        send_WARNING(user, "Veuillez entrer un chiffre en Id")

    username = dbControl.get_username_by_user_id(userId)
    if username == None:
        send_WARNING(user, "Impossible de trouver l'utilisateur")
    else:
        user.send(("USERID " + username + " " + str(userId)))

def NEWMSG(userList, user, channel, content):
    userId = user.get_id()

    if channel == "commands" and (not dbControl.check_mod_by_username(user.get_username())):
        send_WARNING(user, "Vous n'avez pas les permissions requises")
        return
    
    channelId = dbControl.get_channel_id_by_name(channel)
    if userId == None:
        send_WARNING(user, "Vous n'etes pas connecte")
    message = dbControl.send_message(userId, channelId, content)
    # send_SUCCESS(user)

    username = user.get_username()
    msgInfo = dbControl.get_message_info(message)
    for x in userList:
        try:    
            if x.get_id() == user.get_id():
                continue
            # Vérifier que msgInfo est valide avant d'accéder aux indices
            if not msgInfo or len(msgInfo) < 4:
                continue
            #MSG salon sender timestamp contenu_du_message
            x.send(" ".join(["MSG", channel, username, msgInfo[2].replace(" ","_"), content]))
        except:
            pass
    if channel == "commands": admin_command_runner(userList, content)

def LISTMSG(user, channel, offset):
    print("Demande de lecture sur", channel)
    try:
        offset = int(offset)
    except:
        send_WARNING(user, "Offset doit etre un int")
    
    channelId = dbControl.get_channel_id_by_name(channel)

    if channelId == None:
        send_WARNING(user, "Le channel " + channel + " est introuvable")

    msgList = dbControl.read_messages(channelId, offset)
    for row in msgList:
        # row peut être (id,) ou directement un id selon l'appelant
        message_id = row[0] if isinstance(row, (list, tuple)) else row
        msgInfo = dbControl.get_message_info(message_id)
        if not msgInfo or len(msgInfo) < 4:
            continue
        senderName = dbControl.get_username_by_user_id(msgInfo[1])
        timestamp = msgInfo[2].replace(" ","_")
        content = msgInfo[3]
        user.send(" ".join(["MSG", channel, senderName, timestamp, content]))

def NEWPRIVMSG(userList, user, username, content):
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
    
    message = dbControl.send_message(userId, privateChannelId, content)
    send_SUCCESS(user)
    username = user.get_username()
    msgInfo = dbControl.get_message_info(message)
    for x in userList:
        try:
            if x.get_id() == user.get_id():
                continue
            if not x.get_id() == friendId:
                continue
            if not msgInfo or len(msgInfo) < 4:
                continue
            #MSG salon sender timestamp contenu_du_message
            x.send(" ".join(["PRIVMSG", username, username, msgInfo[2].replace(" ","_"), content]))
        except Exception as e:
            send_WARNING(user, e)

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
    for row in msgList:
        message_id = row[0] if isinstance(row, (list, tuple)) else row
        msgInfo = dbControl.get_message_info(message_id)
        if not msgInfo or len(msgInfo) < 4:
            continue
        sender = dbControl.get_username_by_user_id(msgInfo[1])
        timestamp = msgInfo[2].replace(" ","_")
        content = msgInfo[3]
        print("J'aimerais envoyer:", ("PRIVMSG " + username + " " + sender + " " + timestamp + " " + content))
        user.send(("PRIVMSG " + username + " " + sender + " " + timestamp + " " + content))

def CHANNELLIST(user):
    if dbControl.check_mod_by_username(user.get_username()):
        user.send("CHANNEL commands")
    for x in dbControl.get_channel_list():
        if x[1] == "commands": continue
        if x[2] == 0:
            user.send(("CHANNEL " + x[1]))

def PASSWORDEDIT(user, newPassword):
    dbControl.change_password(user.get_id(), newPassword)
    send_SUCCESS(user)

def FRIENDASKED(user):
    userId = user.get_id()
    askedList = dbControl.list_friendships_ids(userId)
    if askedList == None:
        return
    for friendship in askedList:
        if dbControl.is_friendship_pending(friendship):
            friendshipIds = dbControl.get_user_id_by_friendship(friendship)
            # [0] c'est l'id de l'initiateur
            if friendshipIds[0] != userId:
                continue
            friendName = dbControl.get_username_by_user_id(friendshipIds[1])
            user.send("YOUASKED " + friendName)

def ASKEDFRIEND(user):
    userId = user.get_id()
    askedList = dbControl.list_friendships_ids(userId)
    if askedList == None:
        return
    for friendship in askedList:
        if dbControl.is_friendship_pending(friendship):
            friendshipIds = dbControl.get_user_id_by_friendship(friendship)
            # [0] c'est l'id de l'initiateur
            if friendshipIds[1] != userId:
                continue
            friendName = dbControl.get_username_by_user_id(friendshipIds[0])
            user.send("ASKEDYOU " + friendName)

    #ASKEDYOU utilisateur: donne un utilisateur qui a demandé en ami
    #YOUASKED utilisateur: donne un utilisateur qui a été demandé en ami
    #FRIENDASKED: demande la liste des personnes ayant envoyé une demande d'ami
    #ASKEDFRIEND: demande la liste des personnes qu'on a demandé en ami

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
        "argsCount": 1,
        "needUserList": True
    },
    # Oui en fait ca fait sensiblement la meme chose
    "ACCEPTFRIEND": {
        "function": ASKFRIEND,
        "argsCount": 1
    },
    "FRIENDASKED": {
        "function": FRIENDASKED,
        "argsCount": 0
    },
    "ASKEDFRIEND": {
        "function": ASKEDFRIEND,
        "argsCount": 0
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
        "argsCount": 2,
        "needUserList": True
    },
    "LISTMSG": {
        "function": LISTMSG,
        "argsCount": 2
    },
    "NEWPRIVMSG": {
        "function": NEWPRIVMSG,
        "argsCount": 2,
        "needUserList": True
    },
    "LISTPRIVMSG": {
        "function": LISTPRIVMSG,
        "argsCount": 2
    },
    "CHANNELLIST": {
        "function": CHANNELLIST,
        "argsCount": 0
    },
    "PONG": {
        "function": PONG,
        "argsCount": 0
    },
    "PASSWORDEDIT": {
        "function": PASSWORDEDIT,
        "argsCount": 1
    }
}