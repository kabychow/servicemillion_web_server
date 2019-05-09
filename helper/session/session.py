from helper.database import DB
from helper.session.helper.messages import Messages
from helper.session.helper.sequence import Sequence
from helper.session.helper.key_value import KeyValue


class Session:
    def __init__(self, client):
        self.kv = KeyValue({'$client_id': client['id']})
        self.sequence = Sequence(client['flow'])
        self.messages = Messages()

    def save(self):
        response_id = DB().add_response(self.kv.get('$client_id'), self.kv.get())
        return response_id
