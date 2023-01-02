# import socket
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from time import sleep
from Constants import *
import sys

# current server details, adjust accordingly
# HOST = '127.0.0.1'
# PORT = 6667 # commonly chosen IRC port
ADDR = (HOST, PORT)

# constants
# BUFF_SIZE = 512 # limit message size
# crlf = "\r\n"   # signals end of every message
# MOTD = "Welcome to the {}:{} IRC Server! \nType 'STATS m' to list available commands and usages".format(HOST, PORT)

# Data persistence - currently non-persistent
clients = {} # client objects used as key for chosen nickname value
nicknames = {} # nickname key for client object values
addresses = {} # storage of client addresses by client object key
channels = {} # storage of channel objects by name key
threads = {} # storage of thread by client object key

# Utility class for chat rooms
class Channel:
    def __init__(self, name, topic = "No topic."):
        self.name = name
        self.topic = topic
        self.nicknames = []

# main utility method to parse encoded message, return relevant params
def parse(message):
    sender = command = target = body = None
    if not message:
        return sender, command, target, body
    # Decode message
    decode = message.decode('ascii')
    # split into params
    first = decode.split(':')
    # message contains no body
    if len(first) < 3:
        nocolon = first[1]
        terms = nocolon.replace('\r\n', '')
        terms = terms.split(' ')
        # Store terms if they exist
        if len(terms) == 1:
            sender = terms[0]
        elif len(terms) == 2:
            sender = terms[0]
            command = terms[1]
        else:
            sender = terms[0]
            command = terms[1]
            target = terms[2]
    else:
        # message has body
        nocolon = first[1]
        body = first[2]
        terms = nocolon
        terms = terms.split(' ')
        # store terms
        sender = terms[0]
        command = terms[1]
        target = terms[2]
    return sender, command, target, body

# Utility functions to execute given commands

# joins a client to a room
def join(message):
    if not message:
        return 461
    sender, command, target, body = parse(message)
    if not target:
        return 403
    # find nickname
    name = sender
    # add client to channel list
    if target in channels.keys():
        # grab channel object
        channel = channels[target]
        # add name to channel list
        if name:
            if name in channel.nicknames:
                return 443
            else:
                print('adding {} to {}'.format(name, target))
                channel.nicknames.append(name)
    else:
        # create new channel
        print('creating new channel {}'.format(target))
        channel = Channel(target)
        if name:
            # add name to channel's nickname list
            channels[target] = channel
            print('adding {} to {}'.format(name, target))
            channel.nicknames.append(name)
    return None

# list channels and their topics
def list(message):
    sender, command, target, body = parse(message)
    # grab channel
    channel_list = 'List of channels: '
    for channel in channels:
        channel_list += channels[channel].name
        channel_list += ', Topic: {};  '.format(channels[channel].topic)
    channel_list += crlf
    # grab client
    client = nicknames[sender]
    client.send(bytes(channel_list,'ascii'))

# called when client sends message, exits or is disconnected
def quit(message):
    sender, command, target, body = parse(message)
    # remove client from clients and nicknames
    client = nicknames[sender]
    # search channels for sender
    channels_in = []
    for name, obj in channels.items():
        if sender in obj.nicknames:
            obj.nicknames.remove(sender)
            print('Removed {} from {}.'.format(sender, obj.name))
            channels_in.append(name)
            if body:
                broadcast(bytes(':{} QUIT {} :{}\r\n'.format(sender, name, body),'ascii'))
            else:
                broadcast(bytes(':{} QUIT {} :has left the chat\r\n'.format(sender, name),'ascii'))
    # check if channel is empty
    for channel in channels_in:
        if len(channels[channel].nicknames) == 0:
            channels.pop(channel)
            print('{} is empty and has been removed.'.format(channel))
    # notify client if thread is running
    if threads[client].isAlive():
        client.send(bytes("You have been disconnected.",'ascii'))
    # remove user data if exists
    print("client {}: {} has left the server.".format(client,sender))
    clients.pop(client)
    nicknames.pop(sender)
    client.close()
    return None

# send a private message to a channel or client
def privmsg(message):
    sender, command, target, body = parse(message)
    if target:
        return broadcast(message)
    else:
        return 411

# list all channels and nicknames, or one channel and its nicknames
def names(message):
    sender, command, target, body = parse(message)
    client = nicknames[sender]
    # if channel is specified
    if target:
        nick_list = "List of nicknames in {}: ".format(target)
        # grab channel
        channel = channels[target]
        for name in channel.nicknames:
            nick_list += "{}, ".format(name)
    else:
        list(message)
        nick_list = "List of nicknames: "
        for name in nicknames:
            nick_list += '{}, '.format(name)
    client.send(bytes(nick_list,'ascii'))
    return None

# provide client with commands and usage examples
def stats(message):
    # usage = "'LIST' usage: LIST <channel> \n\tEx: 'LIST' lists all channels \n"
    # usage1 = "'PRIVMSG' usage: PRIVMSG <receiver> <text to be sent> \n\tEx: 'PRIVMSG Wiz :Hello!'\n"
    # usage2 = "'NAMES' usage: NAMES <channel> \n\tEx: 'NAMES' lists all channels and users\n"
    # usage3 = "'QUIT' usage: QUIT [<optional message>] \n\tEx: 'QUIT :Gone fishing' exits client and relays message"
    # usage4 = "'PART' usage: PART <channel>{,<channel>} \n\tEx: 'PART #music' user leaves #music chat room"
    # usage5 = "'JOIN' usage: JOIN <channel>{,<channel>} \n\tEx:'JOIN #coolguys,#lesscoolguys' user joins both channels"
    # usages = [usage, usage1, usage2, usage3, usage4, usage5]
    usages = [LIST, PRIVMSG, NAMES, QUIT, PART, JOIN]
    sender, command, target, body = parse(message)
    client = nicknames[sender]
    for line in usages:
        client.send(bytes(line,'ascii'))
        # only used to fully display usages on separate lines,  if removed, sent as single line in GUI
        sleep(0.00005)
    return None

# allows client to leave a given channel, broadcasts to channel members
def part(message):
    sender, command, target, body = parse(message)
    client = nicknames[sender]
    if not target:
        return 461
    elif not target in channels.keys():
        # check if channel exists
        return 403
    else:
        # check if user is in channel
        if not sender in channels[target].nicknames:
            return 442
        # remove user from channel
        channels[target].nicknames.remove(sender)
        # broacast message to channel
        broadcast(message)


# dictionary of int code, error string pairs used as replies
errors = dict([(461, 'ERR_NEEDMOREPARAMS'),(411, 'ERR_NORECIPIENT'),(421,'ERR_UNKNOWNCOMMAND'),(403, 'ERR_NOSUCHCHANNEL'),(402, 'ERR_NOSUCHSERVER'),(443, 'ERROR_USERONCHANNEL'), (433, 'ERR_NICKNAMEINUSE'), (442, 'ERR_NOTONCHANNEL')])
# object of usable commands and their respective utility functions
commands = {'JOIN': join, 'LIST': list, 'PRIVMSG': privmsg, 'QUIT': quit, 'NAMES': names, 'STATS': stats, 'PART': part}

# process and execute a given message
def execute(message):
    sender, command, target, body = parse(message)
    print('executing command:', command)
    result = None
    if command in commands:
        # check if multiple targets
        if target and ',' in target:
            # split target
            targets = target.split(',')
            for t in targets:
                # recompose message for each target
                new_message = ":{} {} {} :{}\r\n".format(sender, command, t, body)
                execute(bytes(new_message,'ascii'))
            return result
        else:
            result = commands[command](message)
    else:
        if not target:
            result = 411
        else:
            result = 421
    return result

# accepts client socket and starts thread
def receive():
    while True:
        try:
            client, client_address = SERVER.accept()
            addresses[client] = client_address
            print("Connected with {}".format(str(client_address)))
            client.send(bytes("Enter your nickname like so: \n 'NICK <chosen name>'",'ascii'))
            threads[client] = Thread(target=handle_client, args=(client,))
            threads[client].start()
        except OSError as e:
            print('exception in receive: {}'.format(e))
            break
        except KeyboardInterrupt:
            break

# Register user nickname while initially handling client
def register(client):
    name = ''
    while not name:
        message = client.recv(BUFF_SIZE).decode('ascii')
        params = message.split(' ')
        # continue in while loop until valid nickname received
        if len(params) == 2:
            command = params[0]
            name = params[1]
            if command == 'NICK' and name:
                name = params[1].replace('\r\n','')
                if nicknames.get(name):
                    print('user already taken')
                    client.send(bytes(errors[433],'ascii'))
                    name = None
                else:
                    print('Nick chosen:',len(name))
                    # store client and nickname
                    clients[client] = name
                    nicknames[name] = client
    return name

# callback method for each client thread - processes client messages
def handle_client(client):
    # Wait until client is registered with a usable nickname
    name = register(client)
    # Welcome user
    client.send(bytes(MOTD, "ascii"))
    print('client {} known as {} has joined the server!'.format(client, name))
    # continue to receive messages from client until they QUIT or are removed
    while True:
        message = client.recv(BUFF_SIZE)
        if message:
            # add prefix to incoming message
            prefix = ":{} ".format(name)
            original = message.decode('ascii')
            message = bytes(prefix + original,'ascii')
            # parse terms
            sender, command, target, body = parse(message)
            if command == 'QUIT':
                # only break out of loop if QUIT is received
                execute(message)
                break
            elif command:
                # process message
                result = execute(message)
                # send error result if int code
                if isinstance(result, int):
                    client.send(bytes(errors[result],'ascii'))
            else:
                # unknown command error
                client.send(bytes(errors[421],'ascii'))
        else:
            # error occured, notify client
            if threads[client].isAlive():
                client.send(bytes("You were disconnected from the server.", "ascii"))
            # create message and call QUIT if unexpected exception closes thread
            message = bytes(":{} QUIT".format(name), "ascii")
            quit(message)
            break

# send message to user or channel
def broadcast(message):
    sender, command, target, body = parse(message)
    print('broadcasting message')
    if target and '#' in target:
        # receiver is channel, check if channel exists
        if channels.get(target):
            channel = channels[target]
            for name in channel.nicknames:
                # grab client and send message
                client = nicknames[name]
                client.send(message)
        else:
            return 403
    elif target:
        # receiver is client, check if client exists
        if nicknames.get(target):
            client = nicknames[target]
            client.send(message)
        else:
            return 411
    else:
        return 411

# create socket
try:
    SERVER = socket(AF_INET, SOCK_STREAM)
    SERVER.bind(ADDR)
except OSError as e:
    print('Error creating socket: {}'.format(e))
    sys.exit(1)

# listen for connections
try:
    while True:
        try:
            SERVER.listen(10)
            print("Waiting for connection...")
            ACCEPT_THREAD = Thread(target=receive)
            ACCEPT_THREAD.start()
            ACCEPT_THREAD.join()
        except socket.error as e:
            print('Error while serving data: {}'.format(e))
            SERVER.close()
            sys.exit(1)
        except KeyboardInterrupt:
            SERVER.close()
            break
except KeyboardInterrupt:
    print('Server forced closed by keyboard interrupt.')
