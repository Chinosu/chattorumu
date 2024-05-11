import socket
import os
import asyncio
from constants import *

if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server_socket.bind(SOCKET_PATH)
server_socket.listen()

print(f"Server listening on {SOCKET_PATH}")

while True:
    connection, client_address = server_socket.accept()
    try:
        print("Connection from", client_address)
        while True:
            data = connection.recv(16)
            if data:
                print("Received:", data.decode())
                connection.sendall(data)
            else:
                break
    finally:
        connection.close()
