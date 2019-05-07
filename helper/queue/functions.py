from helper import database
from helper.queue.queue import Queue

_queue = {}


def get(queue_id):
    return _queue[int(queue_id)]


def add(api_key, name, email, question):
    queue_id = database.add_queue(api_key, name, email, question)
    _queue[queue_id] = Queue(name, email, question)
    return queue_id
