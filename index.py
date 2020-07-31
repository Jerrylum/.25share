#!/usr/bin/env python3

import socket
import _thread
import base64
import sys
import os
import hashlib

from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES

HOST = '0.0.0.0'
PORT = 7984
DEFAULT_ALLOW = False
DEFAULT_MODES = {'typing': False, 'clipboard': False}

RED = '[31m'
GREEN = '[32m'
YELLOW = '[33m'
BLUE = '[34m'
RESET = '[0m'

PONG_FLAG = bytes([3])
COPY_FLAG = bytes([4])


###############################################################################
###############################################################################


class Server:
    def __init__(self):
        random_generator = Random.new().read

        rsa = RSA.generate(1024, random_generator)

        privatePem = rsa.exportKey()
        RSAKey = RSA.importKey(privatePem)
        self.cipher = Cipher_pkcs1_v1_5.new(RSAKey)

        publicPem = rsa.publickey().exportKey()

        # always base64 encoded
        publicPemNoHeader = ''.join(publicPem.decode().split('\n')[1:-1])

        self.firstRSAPublicKeySendOutMessage = bytearray(
            publicPemNoHeader, 'utf8')
        self.binaryPublicKey = base64.b64decode(publicPemNoHeader)

        self.socket = s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)

        self.modes = DEFAULT_MODES
        self.latestClient = None
        self.clients = []
        self._clientCount = 1

    def close(self):
        self.socket.close()

    def addClient(self, client):
        client.id = str(self._clientCount)
        self._clientCount += 1
        self.clients.append(client)

    def removeClient(self, client):
        self.clients.remove(client)


class Client():
    def __init__(self, server, conn, addr):
        self.conn = conn
        self.addr = addr
        self.server = server
        self.allowed = DEFAULT_ALLOW
        self.id = None

    def close(self):
        self.conn.shutdown(socket.SHUT_WR)
        self.conn.close()

    def getAESKey(self):
        encrypted_data = self.conn.recv(128)
        if not encrypted_data:
            raise Exception('0')

        data = self.server.cipher.decrypt(encrypted_data, [])

        self.shareKey = data[0:32]
        self.shareIv = data[32:48]

        m = hashlib.md5()
        m.update(self.server.binaryPublicKey)
        m.update(self.shareKey)
        self.securityCode = m.hexdigest().upper()

    def recvMessage(self):
        encrypted_data = self.conn.recv(2048)
        if not encrypted_data:
            raise Exception('0')

        shareCipher = self._getCipher()
        data = shareCipher.decrypt(encrypted_data)

        return data

    def sendServerPublicKey(self):
        self._send(self.server.firstRSAPublicKeySendOutMessage)

    def sendMessage(self, binary):
        shareCipher = self._getCipher()
        encrypted_data = shareCipher.encrypt(binary)

        self._send(encrypted_data)

    def _send(self, send):
        package_len = len(send).to_bytes(2, sys.byteorder)
        self.conn.sendall(joinBinaryArray(package_len, send))

    def _getCipher(self):
        return AES.new(self.shareKey, AES.MODE_CFB, self.shareIv, segment_size=128)


###############################################################################
###############################################################################


def joinBinaryArray(*args):
    return b''.join(args)


def commandParser(raw):
    def showHelp():
        print("""
COMMAND
    .help                            show this help message
    .chmod <mode>                    change how the server handles messages
    .ls                              list all connected clients
    .allow <client>                  allow client(s) to send messages
    .kick <client>                   kick specified client(s)
    .send <client> <content>         send a message to client(s)
    .stop                            stop the server

CLIENT SELECTOR
    @a      all clients
    @p      the latest client who sent a message / connected
    <ID>    specified client id, e.g. `5`

PERMISSION MODE
    t       Typing text
    c       Clipboard

    e.g. `t`, `c` and `tc` are acceptable

NOTE
    1. Commands must be preceded by a period.
    2. Any input that does not start with a period is understood as sending
       the entire sentence to the latest client (@p).
    3. If you want to send a message that start with a period, use command
       `.send @p YOUR MESSAGE`
""")

    def changeMode(mode):
        usingServer.modes['typing'] = 't' in mode
        usingServer.modes['clipboard'] = 'c' in mode
        print(GREEN + 'Mode changed to', usingServer.modes, RESET)

    def listClients():
        howmany = len(usingServer.clients)
        if howmany == 0:
            print('\nNo client')
        else:
            print('\nTotal of %s client(s):' % (howmany))
            for c in usingServer.clients:
                print('#' + c.id + '\t' + c.addr[0])

    def allowClient(c, arg):
        c.allowed = True
        print(GREEN + 'Accept client #' + c.id, RESET)

    def kickClient(c, arg):
        c.close()
        print(GREEN + 'Kicked #' + c.id, RESET)

    def sendMessage(c, arg):
        c.sendMessage(joinBinaryArray(COPY_FLAG, bytearray(arg[0], 'utf8')))
        print(GREEN + 'Sent to #' + c.id, RESET)

    def stopServer():
        usingServer.close()
        exit(0)
        pass

    def clientSelectorParser(selector, fnc, arg):
        if selector == '@a':
            clients = usingServer.clients
        elif selector == '@p':
            clients = [usingServer.latestClient]
        else:
            thelist = [x for x in usingServer.clients if x.id == selector]
            clients = [thelist and thelist[0] or None]

        for c in clients:
            if c == None:
                raise TypeError('None')
            fnc(c, arg)

    if raw.startswith('.'):
        split = raw.split(' ')

        cmd = split[0][1::1]
        try:
            if cmd == 'help':
                showHelp()
            elif cmd == 'chmod':
                changeMode(split[1])
            elif cmd == 'ls':
                listClients()
            elif cmd == 'allow':
                clientSelectorParser(split[1], allowClient, ())
            elif cmd == 'kick':
                clientSelectorParser(split[1], kickClient, ())
            elif cmd == 'send':
                clientSelectorParser(split[1], sendMessage, (' '.join(split[2::1]),))
            elif cmd == 'stop':
                stopServer()
            else:
                print(RED + 'Unknown command', RESET)
                showHelp()
        except TypeError:
            print(RED + 'Client not found', RESET)
        except Exception:
            print(RED + 'Command exception', RESET)
            showHelp()

    else:
        clientSelectorParser('@p', sendMessage, (raw,))

    print(RESET)  # Important


###############################################################################
###############################################################################


def clientThread(server, conn, addr):
    print(GREEN + '\nConnected by', addr[0], RESET)

    try:
        thisClient = Client(server, conn, addr)
        server.addClient(thisClient)

        ##############

        thisClient.sendServerPublicKey()
        thisClient.getAESKey()

        display = [thisClient.securityCode[i:i+4]
                   for i in range(0, len(thisClient.securityCode), 4)]
        print('Security Code:')
        print(YELLOW + ('%s %s %s %s\n%s %s %s %s\n' % tuple(display)) + RESET)
        print('To ensure your messages are secured, please verify that the security code\n' +
              'displayed on the screen is exactly the same as that displayed on the client.\n')

        if not thisClient.allowed:
            print('Use command' + BLUE + ' .allow ' + thisClient.id + RESET + ' to allow the client to send messages\n')

        ##############

        while True:
            server.latestClient = thisClient

            result = thisClient.recvMessage()

            msgid = result[0:4]
            msg = result[4::1].decode()

            if not thisClient.allowed:
                continue

            print(BLUE + '#' + thisClient.id + '>' + RESET, msg)


            cmd = 'c="%s";' % msg.replace('"', '\\"').replace('$', '\\$')

            trigger = False
            if server.modes['typing']:
                cmd += 'echo $c | xdotool type --file -;'
                trigger = True
            
            if server.modes['clipboard']:
                cmd += 'echo $c | xclip -sel clip'
                trigger = True

            if trigger == True:
                os.system(cmd)

            thisClient.sendMessage(joinBinaryArray(PONG_FLAG, msgid))
    except Exception as e:
        print(RED + 'Disconnected by', addr[0], RESET)
        # print(e)
        pass

    conn.close()
    server.removeClient(thisClient)
    print(RED + 'Closed', addr[0], RESET)


def serverThread():
    global usingServer
    usingServer = Server()

    while True:
        # Establish connection with client.
        newConn, addr = usingServer.socket.accept()
        _thread.start_new_thread(clientThread, (usingServer, newConn, addr))


###############################################################################
###############################################################################


usingServer = None


if __name__ == '__main__':

    print("""
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥  Quarter Share
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥  Use command %s to learn more about the server's
🟥🟥🟥⬜⬜⬜🟥⬜⬜⬜🟥  internal commands
🟥🟥🟥🟥🟥⬜🟥⬜🟥🟥🟥  
🟥🟥🟥⬜⬜⬜🟥⬜⬜⬜🟥  The server is running at 192.168.0.2:7984
🟥🟥🟥⬜🟥🟥🟥🟥🟥⬜🟥  
🟥⬜🟥⬜⬜⬜🟥⬜⬜⬜🟥  
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥  
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥  
🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥
""" % (BLUE + '.help' + RESET))

    try:
        _thread.start_new_thread(serverThread, ())

        while True:
            commandParser(input())
    except KeyboardInterrupt:
        print('Keyboard Inerrupt, Exit')

        if usingServer != None:
            usingServer.close()

        exit()
