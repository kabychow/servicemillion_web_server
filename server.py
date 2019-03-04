import asyncio
import websockets
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


def to_json(data):
    return str(json.dumps(data, ensure_ascii=False))


async def handle_connection(websocket, _):
    client_id = await websocket.recv()
    greetings, screens, description = db.get_client(client_id)

    while True:
        await websocket.send(to_json({'text': greetings, 'options': screens['title']}))
        data = await websocket.recv()
        if data in screens['title']:
            await action_flow(websocket, client_id, screens['screen_id'][screens['title'].index(data)], description)


async def action_flow(websocket, client_id, screen_id, description):
    response = {}

    while True:
        screen = db.get_screen(screen_id)
        await websocket.send(to_json({'text': screen['text'], 'options': screen['options']['text']}))

        if screen['next_screen_id'] is None and len(screen['options']['next_screen_id']) == 0:
            break

        data = await websocket.recv()

        if len(screen['options']['text']) > 0:
            if data not in screen['options']['text']:
                continue
            screen_id = screen['options']['next_screen_id'][screen['options']['text'].index(data)]
            data = screen['options']['value'][screen['options']['text'].index(data)]

            if data == 'bot':
                await action_bot(websocket, description)
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


async def action_bot(websocket, description):
    def normalize(text):
        lemma = nltk.stem.WordNetLemmatizer()
        return [lemma.lemmatize(token) for token in
                nltk.word_tokenize(text.translate(dict((ord(punct), None) for punct in string.punctuation)))]

    sent_tokens = nltk.sent_tokenize(description.lower())

    await websocket.send(to_json({'text': 'Hi, I am AI Bot and I am here to answer your questions!', 'options': []}))
    await websocket.send(to_json({'text': 'If you want to exit, type Bye!', 'options': []}))

    while True:
        user_response = await websocket.recv()
        user_response = str(user_response).lower()
        if user_response in ['hi', 'hello', 'hey', 'yo']:
            await websocket.send(to_json({'text': 'hey', 'options': []}))
        elif user_response in ['thanks', 'thank you']:
            await websocket.send(to_json({'text': 'you are welcome', 'options': []}))
            break
        elif user_response in ['bye']:
            await websocket.send(to_json({'text': 'goodbye!', 'options': []}))
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
                await websocket.send(to_json({'text': 'I am not sure with that', 'options': []}))
                await websocket.send(to_json({'text': 'Do you want to contact customer support?', 'options': ['Yes', 'No']}))
                if await websocket.recv() == 'Yes':
                    await websocket.send(to_json({'text': 'This function is not supported yet!', 'options': []}))
                    break
                else:
                    await websocket.send(to_json({'text': 'Okay', 'options': []}))
            else:
                await websocket.send(to_json({'text': sent_tokens[idx], 'options': []}))
            sent_tokens.remove(user_response)


start_server = websockets.serve(handle_connection, 'localhost', 8844)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

