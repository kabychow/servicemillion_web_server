import secrets
from helper.session.session import Session

_sessions = {}


def get(session_id):
    if session_id in _sessions:
        return _sessions[session_id]


def add(client):
    session_id = secrets.token_hex(8)
    session = Session(client)
    session.messages.add({
        'text': client['flow']['text'],
        'options': client['flow']['type']
    })
    _sessions[session_id] = session
    return session_id, session
