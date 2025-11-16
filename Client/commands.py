import socket
import asyncio
import time


def send_to_server(server, message):
    """Envoie un message au serveur"""
    server.send(message.encode())
    time.sleep(0.1)


# === Handlers de commandes ===

def handle_ping(server, gui):
    """Répond au PING du serveur"""
    send_to_server(server, "PONG")


def handle_channel(server, gui, channelName):
    """Ajoute un canal à la liste"""
    gui.add_channel(channelName)


def handle_success(server, gui):
    """Commande SUCCESS (silencieuse)"""
    pass


def handle_logged(server, gui, username):
    """Définit l'utilisateur connecté"""
    gui.set_username(username)


def handle_message(server, gui, channel, sender, timestamp, content):
    """Traite un message public"""
    msg = {
        "channel": channel,
        "sender": sender,
        "timestamp": timestamp,
        "content": content
    }
    gui.new_msg(msg, "public")


def handle_channel_update(server, gui):
    """Recharge la liste des canaux"""
    gui.set_username(gui.username)


def handle_friend(server, gui, friendName):
    """Ajoute un ami à la liste"""
    gui.add_friend(friendName)


def handle_private_message(server, gui, channel, sender, timestamp, content):
    """Traite un message privé"""
    msg = {
        "channel": channel,
        "sender": sender,
        "timestamp": timestamp,
        "content": content
    }
    gui.new_msg(msg, "private")


def handle_asked_you(server, gui, friendName):
    """Quelqu'un nous a demandé en ami"""
    gui.add_friend(friendName, "askedYou")


def handle_you_asked(server, gui, friendName):
    """Nous avons demandé quelqu'un en ami"""
    gui.add_friend(friendName, "youAsked")


def handle_warning(server, gui, text):
    """Affiche un avertissement"""
    gui._show_warning(text)


# === Configuration des commandes ===

COMMAND_HANDLERS = {
    "PING": (handle_ping, 0),
    "CHANNEL": (handle_channel, 1),
    "SUCCESS": (handle_success, 0),
    "LOGGED": (handle_logged, 1),
    "MSG": (handle_message, 4),
    "CHANUPDATE": (handle_channel_update, 0),
    "FRIEND": (handle_friend, 1),
    "PRIVMSG": (handle_private_message, 4),
    "ASKEDYOU": (handle_asked_you, 1),
    "YOUASKED": (handle_you_asked, 1),
    "WARNING": (handle_warning, 1),
}