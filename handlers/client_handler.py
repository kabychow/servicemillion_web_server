import string
import json
import requests
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from websockets.exceptions import ConnectionClosed
from database import Database

queue = {}


async def handle(socket, _):
    db = Database()
    client = db.get_client(await socket.recv())
    if client is not None:
        while True:
            await flow(socket, db, client)
    socket.close()


async def flow(socket, db, client):
    response = {}
    await socket.send(encode_message(client['greetings'], client['screens']['title']))
    data = await socket.recv()
    if data in client['screens']['title']:
        screen_id = client['screens']['id'][client['screens']['title'].index(data)]
        while True:
            screen = db.get_screen(screen_id)
            await socket.send(encode_message(screen['text'], screen['options']['text']))
            if len(screen['options']['text']) > 0 or screen['next_screen_id'] is not None:
                data = await socket.recv()
                if len(screen['options']['text']) > 0:
                    if data not in screen['options']['text']:
                        continue
                    screen_id = screen['options']['next_screen_id'][screen['options']['text'].index(data)]
                    data = screen['options']['value'][screen['options']['text'].index(data)]
                    if data == 'bot':
                        await bot(socket, db, client)
                else:
                    screen_id = screen['next_screen_id']
                if screen['label'] != '':
                    if screen['is_array'] == 0:
                        response[screen['label']] = data
                    else:
                        if screen['label'] not in response:
                            response[screen['label']] = []
                        response[screen['label']].append(data)
            else:
                break
    if len(response) > 0:
        await save(socket, db, client, response)


async def bot(socket, db, client):
    sent_tokens = nltk.sent_tokenize(client['description'].lower())
    await socket.send(encode_message('Hi, I am AI Bot and I am here to answer your questions!'))
    while True:
        data = str(await socket.recv()).lower()
        if data in ['hi', 'hello', 'hey', 'yo']:
            await socket.send(encode_message('I am AI Bot. Nice to meet you~'))
        elif data in ['ok', 'okay', 'oh', 'k', 'kk', 'no problem', 'can', 'i see', 'lol', 'haha', 'ya', 'yeah']:
            await socket.send(encode_message('Glad that I helped :)'))
        elif data in ['thanks', 'thank you']:
            await socket.send(encode_message('You\'re welcome~'))
            break
        elif data in ['bye']:
            await socket.send(encode_message('Goodbye~'))
            break
        else:
            sent_tokens.append(data)
            vector = TfidfVectorizer(stop_words='english', tokenizer=tokenize).fit_transform(sent_tokens)
            values = cosine_similarity(vector[-1], vector)
            idx = values.argsort()[0][-2]
            flat = values.flatten()
            flat.sort()
            if flat[-2] == 0:
                await socket.send(encode_message('I am not sure with that :('))
                await socket.send(encode_message('Do you want to contact our customer support?', ['Yes', 'No']))
                if await socket.recv() == 'Yes':
                    await ticket(socket, db, client, data)
                    break
                else:
                    await socket.send(encode_message('I am smarter when you ask me questions with simple keywords :)'))
            else:
                await socket.send(encode_message(sent_tokens[idx]))
            sent_tokens.remove(data)


async def ticket(socket, db, client, message):
    await socket.send(encode_message('What is your name?'))
    name = await socket.recv()
    await socket.send(encode_message('What is your email address?'))
    email = await socket.recv()
    ticket_id = db.add_ticket(client['id'], name, email, message)
    await chat(socket, db, client, message, ticket_id)


async def chat(socket, db, client, message, ticket_id):
    queue[ticket_id] = {'socket': socket, '_socket': None, 'messages': [{'reply': False, 'data': message}]}
    await socket.send(encode_message('Waiting for response from customer support team..', ['Cancel']))
    send_message(db.get_fcm_tokens(client['id']), 'chat', 'New customer on queue', 'Tap to join chat')
    try:
        while True:
            data = await socket.recv()
            if queue[ticket_id]['_socket'] is not None:
                if queue[ticket_id]['_socket'].closed:
                    raise ConnectionClosed(1001, '')
                await queue[ticket_id]['_socket'].send(data)
                queue[ticket_id]['messages'].append({'reply': False, 'data': data})
            else:
                if data == 'Cancel':
                    raise ConnectionClosed(1001, '')
                await socket.send(encode_message('Still waiting for response from customer support team..', ['Cancel']))
    except ConnectionClosed:
        db.set_ticket_status(ticket_id, 0)
        send_message(db.get_fcm_tokens(client['id']), 'chat', 'A customer left queue', 'Tap to send email')


async def save(socket, db, client, response):
    tracking_id = db.put_response(client['id'], str(json.dumps(response, ensure_ascii=False)))
    text = 'Tracking ID: #' + str(tracking_id) + '\n'
    for key in response:
        text += '\n' + key + ':'
        if isinstance(response[key], list):
            for i in range(len(response[key])):
                text += '\n ' + str(i + 1) + '. ' + response[key][i]
        else:
            text += '\n ' + response[key]
        text += '\n'
    await socket.send(encode_message(text))


def send_message(fcm_tokens, action, title, body):
    for fcm_token in fcm_tokens:
        requests.post('https://fcm.googleapis.com/fcm/send',
                      json={
                          'to': fcm_token,
                          'priority': 'high',
                          'notification': {
                              'title': title,
                              'body': body
                          },
                          'data': {
                              'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                              'action': action
                          },
                      },
                      headers={'Authorization': 'key=AAAA7UUdxYA:APA91bHHgo3_wYqOzwhOymyK0pBiVMiI4RcOQceyvB'
                                                'vGDNwtUYCUOXsedzUUyWVJSmnwBOcSQmrp0WJFzXflSswXQdn3iWig1w6M'
                                                'fdAWFYuBtdUtfEzDHKhPq7HNJ9V5xIMrswzLXsy0'},
                      )


def tokenize(text):
    lemma = nltk.stem.WordNetLemmatizer()
    return [lemma.lemmatize(token) for token in
            nltk.word_tokenize(text.translate(dict((ord(p), None) for p in string.punctuation)))]


def encode_message(message, options=None):
    if options is None:
        options = []
    return str(json.dumps({
        'text': message,
        'options': options
    }, ensure_ascii=False))
