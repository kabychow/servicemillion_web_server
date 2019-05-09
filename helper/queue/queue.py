from websockets import WebSocketClientProtocol
import typing


class Queue:
    def __init__(self, client_id):
        self.client_id = client_id
        self.socket: typing.Optional[WebSocketClientProtocol] = None
        self.agent_socket: typing.Optional[WebSocketClientProtocol] = None
