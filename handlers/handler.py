from websockets.client import WebSocketClientProtocol
import mysql.connector
import json
from database import Database


class Handler:
    queue = {}

    def __init__(self, socket: WebSocketClientProtocol):
        self.db = Database()
        self.socket = socket

    @staticmethod
    def to_json(data): return str(json.dumps(data, ensure_ascii=False))
