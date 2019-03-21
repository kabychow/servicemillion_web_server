from websockets.exceptions import ConnectionClosed
from handlers.client_handler import queue, encode_message, send_message
import json
from database import Database


async def handle(socket, _):
    db = Database()
    user = db.get_user(socket.request_headers['Authorization'])
    ticket = db.get_ticket(socket.request_headers['Tid'])
    if user is not None and ticket is not None and user['client_id'] == ticket['client_id']:
        await chat(socket, db, user, ticket)
    socket.close()


async def chat(socket, db, user, ticket):
    try:
        if queue[ticket['id']]['_socket'] is None:
            queue[ticket['id']]['_socket'] = socket
            db.set_ticket_user(ticket['id'], user['id'])
            send_message(db.get_fcm_tokens(ticket['client_id']), 'chat', 'Yay!', 'Someone is replying to the customer')
            try:
                while True:
                    data = await socket.recv()
                    await queue[ticket['id']]['socket'].send(encode_message(data))
                    queue[ticket['id']]['messages'].append({'reply': True, 'data': data})
            except ConnectionClosed:
                db.set_ticket_status(ticket['id'], 0)
                await queue[ticket['id']]['socket'].send(encode_message('Chat session ended.', ['Restart']))
                db.put_message(ticket['id'], str(json.dumps(queue[ticket['id']]['messages'], ensure_ascii=False)))
    except KeyError:
        pass
