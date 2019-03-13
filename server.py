import asyncio
import websockets
from websockets.exceptions import ConnectionClosed
import json
import string
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import database as db


async def handle_connection(socket, _):
    data = json.loads(await socket.recv())
    if 'response_id' not in data:
        client = db.get_client(data['client_id'])
        while True:
            await socket.send(to_json({
                'text': client['greetings'],
                'options': client['screens']['title']
            }))
            data = await socket.recv()
            if data in client['screens']['title']:
                index = client['screens']['title'].index(data)
                await action_flow(socket, client, client['screens']['id'][index])
    else:
        try:
            current = queue[data['client_id']][data['response_id']]
            if current['socket'] is not None and current['_socket'] is None:
                current['_socket'] = socket
                while True:
                    try:
                        await current['socket'].send(to_json({'text': await socket.recv(), 'options': []}))
                    except ConnectionClosed:
                        await current['socket'].send(to_json({'text': 'Chat session ended.', 'options': ['Restart']}))
                        break
        except (IndexError, KeyError):
            pass
        finally:
            socket.close()


async def action_flow(socket, client, screen_id):
    response = {}
    while True:
        screen = db.get_screen(screen_id)
        await socket.send(to_json({
            'text': screen['text'],
            'options': screen['options']['text']
        }))
        if screen['is_last']:
            break
        data = await socket.recv()
        if len(screen['options']['text']) > 0:
            if data not in screen['options']['text']:
                continue
            index = screen['options']['text'].index(data)
            screen_id = screen['options']['next_screen_id'][index]
            data = screen['options']['value'][index]
            if data == 'bot':
                await action_bot(socket, client)
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
        response_id = db.put_response(client['id'], to_json(response))
        final = 'Tracking ID: #' + str(response_id) + '\n\n'
        for key in response:
            final += key + ': '
            if isinstance(response[key], list):
                for item in response[key]:
                    final += item + ', '
                final = final[:-2]
            else:
                final += response[key]
            final += '\n'
        await socket.send(to_json({
            'text': final,
            'options': []
        }))



async def action_bot(socket, client):
    def normalize(text):
        lemma = nltk.stem.WordNetLemmatizer()
        return [lemma.lemmatize(token) for token in
                nltk.word_tokenize(text.translate(dict((ord(punct), None) for punct in string.punctuation)))]

    sent_tokens = nltk.sent_tokenize(client['description'].lower())
    await socket.send(to_json({
        'text': 'Hi, I am AI Bot and I am here to answer your questions!',
        'options': []
    }))
    while True:
        data = str(await socket.recv()).lower()
        if data in ['hi', 'hello', 'hey', 'yo']:
            await socket.send(to_json({
                'text': 'Hey',
                'options': []
            }))
        elif data in ['ok', 'okay', 'oh', 'k', 'kk', 'no problem', 'can', 'i see', 'lol', 'haha', 'hahaha', 'ya', 'yeah']:
            await socket.send(to_json({
                'text': 'Yeah',
                'options': []
            }))
        elif data in ['thanks', 'thank you']:
            await socket.send(to_json({
                'text': 'You are welcome',
                'options': []
            }))
            break
        elif data in ['bye']:
            await socket.send(to_json({
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
                await socket.send(to_json({
                    'text': 'I am not sure with that',
                    'options': []
                }))
                await socket.send(to_json({
                    'text': 'Do you want to contact customer support?',
                    'options': ['Yes', 'No']
                }))
                if await socket.recv() == 'Yes':
                    await action_chat(socket, client, data)
                    break
                else:
                    await socket.send(to_json({
                        'text': 'I am smarter when you ask me questions with simple keywords :)',
                        'options': []
                    }))
            else:
                await socket.send(to_json({
                    'text': sent_tokens[idx],
                    'options': []
                }))
            sent_tokens.remove(data)


async def action_chat(socket, client, question):
    await socket.send(to_json({
        'text': 'What is your name?',
        'options': []
    }))
    name = await socket.recv()
    await socket.send(to_json({
        'text': 'What is your email address?',
        'options': []
    }))
    email = await socket.recv()
    if client['id'] not in queue:
        queue[client['id']] = []
    queue[client['id']].append({'socket': socket, '_socket': None, 'name': name, 'email': email, 'question': question})
    index = len(queue[client['id']]) - 1
    # TODO: push notifications to client customer support team
    await socket.send(to_json({
        'text': 'Waiting for response from customer support team...',
        'options': ['Cancel']
    }))
    while True:
        data = await socket.recv()
        if queue[client['id']][index]['_socket'] is None:
            if data == 'Cancel':
                break
            else:
                await socket.send(to_json({
                    'text': 'Waiting for response from customer support team...',
                    'options': ['Cancel']
                }))
        else:
            if queue[client['id']][index]['_socket'].closed:
                break
            await queue[client['id']][index]['_socket'].send(data)


def to_json(data): return str(json.dumps(data, ensure_ascii=False))


queue = {}
start_server = websockets.serve(handle_connection, port=8844)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

