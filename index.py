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

PONG_FLAG = bytes([3])
COPY_FLAG = bytes([4])

usingSocket = None
latestClient = None

random_generator = Random.new().read

server_rsa = RSA.generate(1024, random_generator)

serverPrivatePem = server_rsa.exportKey()
serverRSAKey = RSA.importKey(serverPrivatePem)
serverCipher = Cipher_pkcs1_v1_5.new(serverRSAKey)

serverPublicPem = server_rsa.publickey().exportKey()
serverPublicPemWithoutHeader = ''.join(serverPublicPem.decode().split('\n')[
                                       1:-1])  # always base64 encoded
serverFirstRSAPublicKeySendOutMessage = bytearray(
    serverPublicPemWithoutHeader, 'utf8')


class Client():
    def __init__(self, conn):
        self.conn = conn

    def getAESKey(self):
        encrypted_data = self.conn.recv(2048)
        if not encrypted_data:
            raise Exception('0')

        data = serverCipher.decrypt(encrypted_data, [])

        self.shareKey = data[0:32]
        self.shareIv = data[32:48]

        # TODO remove this and make a better print
        print('Share AES Key:', self.shareKey.hex())

    def recvMessage(self):
        encrypted_data = self.conn.recv(2048)
        if not encrypted_data:
            raise Exception('0')

        shareCipher = self._getCipher()
        data = shareCipher.decrypt(encrypted_data)

        return data

    def sendServerPublicKey(self):
        self._send(serverFirstRSAPublicKeySendOutMessage)

    def sendMessage(self, binary):
        shareCipher = self._getCipher()
        encrypted_data = shareCipher.encrypt(binary)

        self._send(encrypted_data)

    def _send(self, send):
        package_len = len(send).to_bytes(2, sys.byteorder)
        self.conn.sendall(joinBinaryArray(package_len, send))

    def _getCipher(self):
        return AES.new(self.shareKey, AES.MODE_CFB, self.shareIv, segment_size=128)


def joinBinaryArray(*args):
    return b''.join(args)


def on_new_client(conn, addr):
    global latestClient

    print(GREEN + 'Connected by', addr, RESET)

    try:
        thisClient = Client(conn)

        ##############

        thisClient.sendServerPublicKey()
        thisClient.getAESKey()

        ##############

        while True:
            latestClient = thisClient

            result = thisClient.recvMessage()

            msgid = result[0:4]
            msg = result[4::1].decode()

            print('#' + msgid.hex(), msg)
            # TODO handle the message

            thisClient.sendMessage(joinBinaryArray(PONG_FLAG, msgid))
    except Exception as e:
        print(RED + 'Disconnected by', addr, RESET)
        print(e)
        pass

    conn.close()
    print(RED + 'Closed', addr, RESET)


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
                latestClient.sendMessage(joinBinaryArray(
                    COPY_FLAG, bytearray(answer, 'utf8')))
                print(GREEN + 'Sent', RESET)
    except KeyboardInterrupt:
        print('Keyboard Inerrupt, Exit')
        usingSocket.close()

        exit()
