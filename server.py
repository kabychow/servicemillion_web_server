from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import database as db
import json


def handle_connection(connection: socket):
    response = {}

    try:
        client_id, greetings, screens = db.get_client(receive(connection))

        while True:
            send(connection, {
                'text': greetings,
                'options': screens['title']
            })
            action = receive(connection)

            if action in screens['title']:
                current_screen_id = screens['screen_id'][screens['title'].index(action)]

                while True:
                    screen = db.get_screen(current_screen_id)
                    send(connection, {'text': screen['text'], 'options': screen['options']['text']})

                    if screen['next_screen_id'] is None and len(screen['options']['next_screen_id']) == 0:
                        break

                    data = receive(connection)

                    if len(screen['options']['text']) > 0:
                        if data not in screen['options']['text']:
                            continue
                        current_screen_id = screen['options']['next_screen_id'][screen['options']['text'].index(data)]
                        data = screen['options']['value'][screen['options']['text'].index(data)]

                        if data == 'bot':
                            send(connection,
                                 {'text': 'Hello, I am AI bot. I am here to answer your questions', 'options': []})

                            while True:
                                receive(connection)
                                send(connection, {'text': 'I am not sure I understand your questions', 'options': []})

                    else:
                        current_screen_id = screen['next_screen_id']

                    if screen['label'] != '':
                        if screen['is_array'] == 0:
                            response[screen['label']] = data
                        else:
                            if screen['label'] not in response:
                                response[screen['label']] = []
                            response[screen['label']].append(data)

                if len(response) > 0:
                    db.put_response(client_id, to_json(response))


    except (BrokenPipeError, IOError):
        connection.close()


def accept_connections():
    while True:
        connection, _ = server.accept()
        Thread(target=handle_connection, args=(connection,)).start()


def receive(connection: socket, buffer_size=1024):
    return connection.recv(buffer_size).decode('utf8')


def send(connection: socket, data):
    connection.send(bytes(to_json(data)))


def to_json(data):
    return json.dumps(data, ensure_ascii=False).encode('utf8')


server = socket(AF_INET, SOCK_STREAM)
server.bind(('', 8844))
server.listen(128)
print("Waiting for connection...")
accept_thread = Thread(target=accept_connections)
accept_thread.start()
accept_thread.join()
server.close()
