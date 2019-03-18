import mysql.connector as mariadb
import config


class Database:
    def __init__(self):
        self.db = mariadb.connect(user=config.DB_USER, password=config.DB_PASSWORD, database='superceed')

    def get_client(self, client_id):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute('SELECT id, greetings, description FROM client WHERE id=%s', (client_id,))
        client = cursor.fetchone()
        client['screens'] = {'id': [], 'title': []}
        cursor.execute('SELECT title, screen_id FROM client_screen WHERE client_id=%s', (client_id,))
        for screen in cursor.fetchall():
            client['screens']['id'].append(screen['screen_id'])
            client['screens']['title'].append(screen['title'])
        cursor.close()
        return client

    def get_screen(self, screen_id):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute('SELECT title, text, label, is_array, next_screen_id FROM screen WHERE id=%s', (screen_id,))
        screen = cursor.fetchone()
        screen['options'] = {'text': [], 'value': [], 'next_screen_id': []}
        cursor.execute('SELECT text, value, next_screen_id FROM screen_option WHERE screen_id=%s', (screen_id,))
        for option in cursor.fetchall():
            screen['options']['text'].append(option['text'])
            screen['options']['value'].append(option['value'])
            screen['options']['next_screen_id'].append(option['next_screen_id'])
        cursor.close()
        return screen

    def put_response(self, client_id, data):
        cursor = self.db.cursor()
        cursor.execute('INSERT INTO response(client_id, data) VALUES(%s, %s)', (client_id, data))
        response_id = cursor.lastrowid
        cursor.close()
        self.db.commit()
        return response_id

    def get_fcm_tokens(self,client_id):
        fcm_tokens = []
        cursor = self.db.cursor()
        cursor.execute('SELECT fcm_token FROM client_user WHERE client_id=%s AND status=1', (client_id,))
        for fcm_token, in cursor.fetchall():
            fcm_tokens.append(fcm_token)
        cursor.close()
        return fcm_tokens