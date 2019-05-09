from helper.database import DB
from helper.queue.queue import Queue

queues = {}


def get(queue_id) -> Queue:
    return queues.get(int(queue_id))


def add(client_id, name, email, question):
    queue_id = DB().add_queue(client_id, name, email, question)
    queues[queue_id] = Queue(client_id)
    return queue_id
