#!/usr/bin/env python3

import socket
import _thread
import base64
import sys

from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES

HOST = '0.0.0.0'
PORT = 7984

RED = '[31m'
GREEN = '[32m'
RESET = '[0m'

usingSocket = None
latestClient = None

random_generator = Random.new().read

server_rsa = RSA.generate(1024, random_generator)

serverPrivatePem = server_rsa.exportKey()
serverRSAKey = RSA.importKey(serverPrivatePem)
serverCipher = Cipher_pkcs1_v1_5.new(serverRSAKey)

serverPublicPem = server_rsa.publickey().exportKey()
serverPublicPemWithoutHeader = ''.join(serverPublicPem.decode().split('\n')[1:-1]) # always base64 encoded
serverFirstRSAPublicKeySendOutMessage = bytearray('rsa<' + serverPublicPemWithoutHeader, 'utf8')

class Client():
    def __init__(self, conn):
        self.conn = conn
    
    def getAESKey(self):
        encrypted_data = self.conn.recv(2048)
        if not encrypted_data:
            raise Exception('0')

        data = serverCipher.decrypt(encrypted_data, 123)

        result = data.decode().split('>')

        msg_type = result[0]
        msg = result[1]

        if (msg_type == 'aeskey'):
            self.shareKey = base64.decodebytes(msg.encode())
        
            print('Share AES Key:', self.shareKey.hex()) # TODO remove this and make a better print
        

    def recvMessage(self):
        encrypted_data = self.conn.recv(2048)
        if not encrypted_data:
            raise Exception('0')
    
        shareCipher = AES.new(self.shareKey, AES.MODE_CFB, bytes('ABCDEFGHIJKLMNOP', 'ascii'), segment_size=128)
        data = shareCipher.decrypt(encrypted_data)

        return data

    def sendServerPublicKey(self):
        self._send(serverFirstRSAPublicKeySendOutMessage)

    def sendMessage(self, msg):
        shareCipher = AES.new(self.shareKey, AES.MODE_CFB, bytes('ABCDEFGHIJKLMNOP', 'ascii'), segment_size=128)
        encrypted_data = shareCipher.encrypt(bytearray(msg, 'utf8'))

        self._send(encrypted_data)

    def _send(self, send):
        self.conn.sendall(b''.join([len(send).to_bytes(2, sys.byteorder), send]))


def on_new_client(conn, addr):
    global latestClient

    print(GREEN + 'Connected by', addr, RESET)

    thisClient = Client(conn)

    ##############

    thisClient.sendServerPublicKey()
    thisClient.getAESKey()

    ##############

    while True:
        latestClient = thisClient

        result = thisClient.recvMessage().decode().split('>')

        msg_type = result[0]
        msg = result[1]

        msgid = msg_type

        print('#' + msgid[0:6], msg)
        # TODO handle the message

        thisClient.sendMessage('pong<' + msgid)

    conn.close()
    print(RED + 'Disconnected by', addr, RESET)


def server_thread():
    global usingSocket
    usingSocket = socket.socket()
    usingSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    usingSocket.bind((HOST, PORT))
    usingSocket.listen(5)
    while True:
        c, addr = usingSocket.accept()     # Establish connection with client.
        _thread.start_new_thread(on_new_client, (c, addr))


if __name__ == '__main__':
    try:
        _thread.start_new_thread(server_thread, ())

        while True:
            answer = input()
            if (latestClient != None):
                latestClient.sendMessage('copy<' + answer)
                print(GREEN + 'Sent', RESET)
    except KeyboardInterrupt:
        print('Keyboard Inerrupt, Exit')
        usingSocket.close()

        exit()
