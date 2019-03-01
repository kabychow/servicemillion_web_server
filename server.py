from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import json
import string
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import database as db
import warnings
warnings.filterwarnings("ignore")

#nltk.download('punkt')
#nltk.download('wordnet')
#nltk.download('stopwords')


def handle_connection(connection: socket):
    try:
        client_id = receive(connection)
        greetings, screens, description = db.get_client(client_id)

        while True:
            send(connection, {'text': greetings, 'options': screens['title']})
            data = receive(connection)
            if data in screens['title']:
                action_flow(connection, client_id, screens['screen_id'][screens['title'].index(data)], description)

    except (BrokenPipeError, IOError):
        connection.close()


def action_flow(connection: socket, client_id, screen_id, description):
    response = {}

    while True:
        screen = db.get_screen(screen_id)
        send(connection, {'text': screen['text'], 'options': screen['options']['text']})

        if screen['next_screen_id'] is None and len(screen['options']['next_screen_id']) == 0:
            break

        data = receive(connection)

        if len(screen['options']['text']) > 0:
            if data not in screen['options']['text']:
                continue
            screen_id = screen['options']['next_screen_id'][screen['options']['text'].index(data)]
            data = screen['options']['value'][screen['options']['text'].index(data)]

            if data == 'bot':
                action_bot(connection, description)
        else:
            screen_id = screen['next_screen_id']

        if screen['label'] != '':
            if screen['is_array'] == 0:
                response[screen['label']] = data
            else:
                if screen['label'] not in response:
                    response[screen['label']] = []
                response[screen['label']].append(data)

    if len(response) > 0:
        db.put_response(client_id, to_json(response))


def action_bot(connection: socket, description):
    def normalize(text):
        lemma = nltk.stem.WordNetLemmatizer()
        return [lemma.lemmatize(token) for token in
                nltk.word_tokenize(text.translate(dict((ord(punct), None) for punct in string.punctuation)))]

    sent_tokens = nltk.sent_tokenize(description.lower())

    send(connection, {'text': 'Hi, I am AI Bot and I am here to answer your questions!', 'options': []})
    send(connection, {'text': 'If you want to exit, type Bye!', 'options': []})

    while True:
        user_response = receive(connection).lower()
        if user_response in ['hi', 'hello', 'hey', 'yo']:
            send(connection, {'text': 'hey', 'options': []})
        elif user_response in ['thanks', 'thank you']:
            send(connection, {'text': 'you are welcome', 'options': []})
            break
        elif user_response in ['bye']:
            send(connection, {'text': 'goodbye!', 'options': []})
            break
        else:
            sent_tokens.append(user_response)
            vector = TfidfVectorizer(tokenizer=normalize, stop_words='english').fit_transform(sent_tokens)
            values = cosine_similarity(vector[-1], vector)
            idx = values.argsort()[0][-2]
            flat = values.flatten()
            flat.sort()
            req_vector = flat[-2]
            if req_vector == 0:
                send(connection, {'text': 'I am not sure with that', 'options': []})
                send(connection, {'text': 'Do you want to contact customer support?', 'options': ['Yes', 'No']})
                if receive(connection) == 'Yes':
                    send(connection, {'text': 'This function is not supported yet...', 'options': []})
                    break
                else:
                    send(connection, {'text': 'Okay', 'options': []})
            else:
                send(connection, {'text': sent_tokens[idx], 'options': []})
            sent_tokens.remove(user_response)


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
