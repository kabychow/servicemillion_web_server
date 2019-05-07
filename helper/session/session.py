from helper import database
from helper.session.helper.messages import Messages
from helper.session.helper.sequence import Sequence
from helper.session.helper.key_value import KeyValue


class Session:
    def __init__(self, client):
        self.kv = KeyValue({'$api_key': client['api_key']})
        self.sequence = Sequence(client['flow'])
        self.messages = Messages()

    def save(self):
        response_id = database.add_response(self.kv.get('$api_key'), self.kv.get())
        return response_id
