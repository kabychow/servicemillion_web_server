from helper import queue, fcm
from helper.database import DB
from websockets.exceptions import ConnectionClosed


async def handle_agent(socket, _):
    api_key = socket.request_headers['Authorization']
    queue_id = socket.request_headers['QueueID']
    user = DB().get_user(api_key)
    if user is not None:
        current = queue.get(queue_id)
        if current is not None:
            current.agent_socket = socket
            try:
                while True:
                    data = await socket.recv()
                    await current.socket.send(data)
            except ConnectionClosed:
                if current.socket is not None and not current.socket.closed:
                    await current.socket.close()
                    DB().delete_queue(queue_id)
                    fcm.send(current.client_id)


async def handle_customer(socket, _):
    queue_id = await socket.recv()
    current = queue.get(queue_id)
    if current is not None and current.socket is None:
        current.socket = socket
        DB().set_queue_status(queue_id, 1)
        try:
            while True:
                data = await socket.recv()
                await current.agent_socket.send(data)
        except ConnectionClosed:
            DB().set_queue_status(queue_id, 0)
            fcm.send(current.client_id)
            if current.agent_socket is not None and not current.agent_socket.closed:
                await current.agent_socket.close()
