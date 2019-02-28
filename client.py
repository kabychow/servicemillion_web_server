from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread


def receive():
    while True:
        data = client_socket.recv(1024).decode('utf8')
        if data != '':
            print(data)


client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(('khaibin.asuscomm.com', 8844))
client_socket.send(b'2')
Thread(target=receive).start()

while True:
    msg = input()
    client_socket.send(bytes(msg, 'utf8'))
