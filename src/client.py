import socket
import getpass
from constants import *

client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client_socket.connect(SOCKET_PATH)

try:
    message = f"Hello, UDS from {getpass.getuser()}!"
    print(f"Sending: {message}")
    client_socket.sendall(message.encode())

    amount_received = 0
    amount_expected = len(message)

    while amount_received < amount_expected:
        data = client_socket.recv(16)
        amount_received += len(data)
        print(f"Received: {data.decode()}")
finally:
    client_socket.close()
