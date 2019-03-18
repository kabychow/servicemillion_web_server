import asyncio
import json
import string
import uuid
import websockets
import nltk
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import config
from database import Database

queue = {}


class Handler:
    @staticmethod
    async def handle(socket, _):
        handler = Handler(socket)
        await handler.init()

    def __init__(self, socket):
        self.db = Database()
        self.socket = socket
        self.client = None
        self.reply_id = None
        self.response = {}

    async def init(self):
        data = json.loads(await self.socket.recv())
        self.client = self.db.get_client(data['client_id'])
        if 'reply_id' in data:
            self.reply_id = data['reply_id']
            await self.action_reply()
        else:
            await self.action_flow()

    async def action_reply(self):
        current = queue[self.client['id']][self.reply_id]
        if current['socket'] is not None and current['_socket'] is None:
            current['_socket'] = self.socket
            while True:
                try:
                    await current['socket'].send(to_json({
                        'text': await self.socket.recv(),
                        'options': []
                    }))
                except websockets.exceptions.ConnectionClosed:
                    await current['socket'].send(to_json({
                        'text': 'Chat session ended.',
                        'options': ['Restart']
                    }))
                    break
        self.socket.close()

    async def action_flow(self):
        while True:
            await self.socket.send(to_json({
                'text': self.client['greetings'],
                'options': self.client['screens']['title']
            }))
            data = await self.socket.recv()
            if data in self.client['screens']['title']:
                screen_id = self.client['screens']['id'][self.client['screens']['title'].index(data)]
                while True:
                    screen = self.db.get_screen(screen_id)
                    await self.socket.send(to_json({
                        'text': screen['text'],
                        'options': screen['options']['text']
                    }))
                    if len(screen['options']['text']) == 0 and screen['next_screen_id'] is None:
                        break
                    data = await self.socket.recv()
                    if len(screen['options']['text']) > 0:
                        if data not in screen['options']['text']:
                            continue
                        screen_id = screen['options']['next_screen_id'][screen['options']['text'].index(data)]
                        data = screen['options']['value'][screen['options']['text'].index(data)]
                        if data == 'bot':
                            await self.action_bot()
                    else:
                        screen_id = screen['next_screen_id']
                    if screen['label'] != '':
                        if screen['is_array'] == 0:
                            self.response[screen['label']] = data
                        else:
                            if screen['label'] not in self.response:
                                self.response[screen['label']] = []
                            self.response[screen['label']].append(data)
                if len(self.response) > 0:
                    response_id = self.db.put_response(self.client['id'], to_json(self.response))
                    tracking_message = 'Tracking ID: #' + str(response_id) + '\n'
                    for key in self.response:
                        tracking_message += '\n' + key + ':'
                        if isinstance(self.response[key], list):
                            for i in range(len(self.response[key])):
                                tracking_message += '\n ' + str(i+1) + '. ' + self.response[key][i]
                        else:
                            tracking_message += '\n ' + self.response[key]
                        tracking_message += '\n'
                    await self.socket.send(to_json({
                        'text': tracking_message,
                        'options': []
                    }))

    async def action_bot(self):
        def normalize(text):
            lemma = nltk.stem.WordNetLemmatizer()
            return [lemma.lemmatize(token) for token in
                    nltk.word_tokenize(text.translate(dict((ord(punct), None) for punct in string.punctuation)))]

        sent_tokens = nltk.sent_tokenize(self.client['description'].lower())
        await self.socket.send(to_json({
            'text': 'Hi, I am AI Bot and I am here to answer your questions!',
            'options': []
        }))
        while True:
            data = str(await self.socket.recv()).lower()
            if data in ['hi', 'hello', 'hey', 'yo']:
                await self.socket.send(to_json({
                    'text': 'Hey',
                    'options': []
                }))
            elif data in ['ok', 'okay', 'oh', 'k', 'kk', 'no problem', 'can', 'i see', 'lol', 'haha', 'hahaha', 'ya',
                          'yeah']:
                await self.socket.send(to_json({
                    'text': 'Yeah',
                    'options': []
                }))
            elif data in ['thanks', 'thank you']:
                await self.socket.send(to_json({
                    'text': 'You are welcome',
                    'options': []
                }))
                break
            elif data in ['bye']:
                await self.socket.send(to_json({
                    'text': 'Goodbye!',
                    'options': []
                }))
                break
            else:
                sent_tokens.append(data)
                vector = TfidfVectorizer(stop_words='english', tokenizer=normalize).fit_transform(sent_tokens)
                values = cosine_similarity(vector[-1], vector)
                idx = values.argsort()[0][-2]
                flat = values.flatten()
                flat.sort()
                if flat[-2] == 0:
                    await self.socket.send(to_json({
                        'text': 'I am not sure with that',
                        'options': []
                    }))
                    await self.socket.send(to_json({
                        'text': 'Do you want to contact customer support?',
                        'options': ['Yes', 'No']
                    }))
                    if await self.socket.recv() == 'Yes':
                        await self.action_chat(data)
                        break
                    else:
                        await self.socket.send(to_json({
                            'text': 'I am smarter when you ask me questions with simple keywords :)',
                            'options': []
                        }))
                else:
                    await self.socket.send(to_json({
                        'text': sent_tokens[idx],
                        'options': []
                    }))
                sent_tokens.remove(data)

    async def action_chat(self, message):
        await self.socket.send(to_json({
            'text': 'What is your name?',
            'options': []
        }))
        name = await self.socket.recv()
        await self.socket.send(to_json({
            'text': 'What is your email address?',
            'options': []
        }))
        email = await self.socket.recv()
        if self.client['id'] not in queue:
            queue[self.client['id']] = {}
        chat_id = uuid.uuid4().hex
        queue[self.client['id']][chat_id] = {'socket': self.socket, '_socket': None, 'messages': [message]}
        await self.socket.send(to_json({
            'text': 'Waiting for response from customer support team...',
            'options': ['Cancel']
        }))
        for fcm_token in self.db.get_fcm_tokens(self.client['id']):
            requests.post('https://fcm.googleapis.com/fcm/send',
                          headers={'Authorization': 'key=' + config.FCM_API_KEY},
                          json={
                              'to': fcm_token,
                              'priority': 'high',
                              'notification': {
                                  'title': name,
                                  'body': message
                              },
                              'data': {
                                  'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                                  'id': chat_id,
                                  'name': name,
                                  'email': email,
                                  'message': message
                              },
                          })
        while True:
            data = await self.socket.recv()
            if queue[self.client['id']][chat_id]['_socket'] is None:
                if data == 'Cancel':
                    break
                else:
                    await self.socket.send(to_json({
                        'text': 'Waiting for response from customer support team...',
                        'options': ['Cancel']
                    }))
            else:
                if queue[self.client['id']][chat_id]['_socket'].closed:
                    break
                await queue[self.client['id']][chat_id]['_socket'].send(await self.socket.recv())


def to_json(data): return str(json.dumps(data, ensure_ascii=False))


asyncio.get_event_loop().run_until_complete(websockets.serve(Handler.handle, port=8844))
asyncio.get_event_loop().run_forever()
