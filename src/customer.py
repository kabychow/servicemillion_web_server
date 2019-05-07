from helper import queue


async def handle(socket, _):
    queue_id = await socket.recv()
    current = queue.get(queue_id)
    if current.socket is None:
        current.socket = socket
