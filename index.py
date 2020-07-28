#!/usr/bin/env python3

import socket
import _thread


HOST = '0.0.0.0'
PORT = 7984

RED = '[31m'
GREEN = '[32m'
RESET = '[0m'

usingSocket = None
latestConn = None

def on_new_client(conn, addr):
    global latestConn

    print(GREEN + 'Connected by', addr, RESET)
    while True:
        latestConn = conn

        data = conn.recv(1024)
        if not data:
            break

        result = data.decode()[0:-1].split('>')

        msgid = result[0]
        msg = result[1]

        print(msgid[0:6] + '>>' + msg + '<<')

        conn.sendall(bytearray('pong<' + msgid + '\n', 'utf8'))
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
            if (latestConn != None):
                latestConn.sendall(bytearray('copy<' + answer + '\n', 'utf8'))
                print(GREEN + 'Sent', RESET)
    except KeyboardInterrupt:
        print('Keyboard Inerrupt, Exit')
        usingSocket.close()

        exit()
