from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import json
import random
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
    def greeting(sentence):
        for word in sentence.split():
            if word.lower() in GREETING_INPUTS:
                return random.choice(GREETING_RESPONSES)

    def response(user_response):
        robo_response = ''
        sent_tokens.append(user_response)
        TfidfVec = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english')
        tfidf = TfidfVec.fit_transform(sent_tokens)
        vals = cosine_similarity(tfidf[-1], tfidf)
        idx = vals.argsort()[0][-2]
        flat = vals.flatten()
        flat.sort()
        req_tfidf = flat[-2]
        if req_tfidf == 0:
            robo_response = robo_response + "I am sorry! I don't understand you"
            return robo_response
        else:
            robo_response = robo_response + sent_tokens[idx]
            return robo_response

    def LemTokens(tokens):
        return [lemmer.lemmatize(token) for token in tokens]

    def LemNormalize(text):
        return LemTokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))

    description = description.lower()

    sent_tokens = nltk.sent_tokenize(description)
    lemmer = nltk.stem.WordNetLemmatizer()

    remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)

    GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up", "hey",)
    GREETING_RESPONSES = ["hi", "hey", "hi there", "hello", "I am glad! You are talking to me"]

    flag = True
    send(connection, {'text': 'Hi, I am AI Bot and I am here to answer your questions!', 'options': []})
    send(connection, {'text': 'If you want to exit, type Bye!', 'options': []})

    while flag:
        user_response = receive(connection)
        user_response = user_response.lower()
        if user_response != 'bye':
            if user_response == 'thanks' or user_response == 'thank you':
                flag = False
                send(connection, {'text': 'You are welcome..', 'options': []})
            else:
                if greeting(user_response) is not None:
                    send(connection, {'text': greeting(user_response), 'options': []})
                else:
                    send(connection, {'text': response(user_response), 'options': []})
                    sent_tokens.remove(user_response)
        else:
            flag = False
            send(connection, {'text': 'Bye', 'options': []})


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
