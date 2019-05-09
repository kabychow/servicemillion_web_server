import os
import requests
from threading import Thread
from helper.database import DB


def send(client_id, data=None, title=None, body=None):
    Thread(target=start, args=(client_id, data, title, body)).start()


def start(client_id, data=None, title=None, body=None):
    if data is None:
        data = {}
    data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'

    target_users = DB().get_all_users(client_id)

    with open(os.path.join(os.path.dirname(__file__), 'auth.key')) as file:
        key = file.read()
        for target_user in target_users:
            r = requests.post('https://fcm.googleapis.com/fcm/send', headers={'Authorization': 'key={}'.format(key)},
                              json={'to': target_user['fcm_token'], 'priority': 'high',
                                    'notification': {'title': title, 'body': body},
                                    'data': data})
