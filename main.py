import socket
import asyncio
import dbControl
from commands import *
from classes import *

users = []
debug = False

async def command_receiver(user):
    while user.isActive:
        try:
            received = await asyncio.get_running_loop().sock_recv(user.socket, 1024)
            if not received:
                user.disconnect()
                return
        except ConnectionAbortedError:
            user.disconnect()
            return
        
        command = received.decode().replace("\r\n","").split(" ")
        command_runner(user, command)

def command_runner(user, command):
    global debug
    if not command:
        return

    if command[0].upper() == "EXIT":
        exit()

    if command[0].upper() == "DEBUG":
        debug = True

    if command[0].upper() == "HELP":
        commandList["HELP"]["function"](user, commandList)
        return

    usedCommand = commandList.get(command[0].upper(), "wrong_command")

    if usedCommand == "wrong_command":
        commandList[usedCommand]["function"](user)
        return
    else:
        args_count = usedCommand.get("argsCount", 0)

    if len(command) - 1 > args_count:
        fixed_args = command[1:args_count]
        last_arg = " ".join(command[args_count:])
        commandArgs = [user, *fixed_args, last_arg]
    else:
        commandArgs = [user, *command[1:args_count + 1]]

    if len(commandArgs)-1 != usedCommand["argsCount"]:
        send_WARNING(user, "Nombre d'arguments incorrect")
        return

    try:
        usedCommand["function"](*commandArgs)
    except Exception as e:
        send_WARNING(user, "Erreur: " + str(e))


async def client_accept():
    serversocket.setblocking(False)
    loop = asyncio.get_running_loop()

    while True:
        clientsocket, address = await loop.sock_accept(serversocket)
        print("Connection reçue:", address)
        clientsocket.setblocking(False)

        user = User(clientsocket)
        users.append(user)

        asyncio.create_task(command_receiver(user))

isCommandChannel = False
for x in dbControl.get_channel_list():
    if x[1] == "commands":
        isCommandChannel = True

if not isCommandChannel:
    dbControl.new_channel("commands", False, 0)

if dbControl.get_user_id_by_username("SERVER") == None: dbControl.register("SERVER", "SERVER", 0)

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(("0.0.0.0", 484))
serversocket.listen(5)

print("En attente de connections...")

asyncio.run(client_accept())