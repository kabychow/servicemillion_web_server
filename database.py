import mysql.connector as mariadb


class Database:
    def __init__(self):
        self.db = mariadb.connect(user='root', password='', database='superceed')

    def init(self):
        cursor = self.db.cursor()
        cursor.execute('UPDATE ticket SET status = 0')
        cursor.close()
        self.db.commit()

    def get_user(self, api_key):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute('SELECT id, client_id FROM user WHERE api_key = %s',
                       (api_key,))
        user = cursor.fetchone()
        cursor.close()
        return user

    def add_ticket(self, client_id, name, email, message):
        cursor = self.db.cursor()
        cursor.execute('INSERT INTO ticket(client_id, name, email, message) VALUES(%s, %s, %s, %s)',
                       (client_id, name, email, message))
        ticket_id = cursor.lastrowid
        cursor.close()
        self.db.commit()
        return ticket_id

    def get_ticket(self, ticket_id):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute('SELECT id, client_id FROM ticket WHERE id = %s AND user_id IS NULL AND status = 1',
                       (ticket_id,))
        ticket = cursor.fetchone()
        cursor.close()
        return ticket

    def set_ticket_status(self, ticket_id, status):
        cursor = self.db.cursor()
        cursor.execute('UPDATE ticket SET status = %s WHERE id = %s',
                       (status, ticket_id))
        cursor.close()
        self.db.commit()

    def set_ticket_user(self, ticket_id, user_id):
        cursor = self.db.cursor()
        cursor.execute('UPDATE ticket SET user_id = %s WHERE id = %s',
                       (user_id, ticket_id))
        cursor.close()
        self.db.commit()

    def get_client(self, api_key):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute('SELECT id, greetings, description FROM client WHERE api_key=%s',
                       (api_key,))
        client = cursor.fetchone()
        client['screens'] = {'id': [], 'title': []}
        cursor.execute('SELECT title, screen_id FROM client_screen WHERE client_id=%s',
                       (client['id'],))
        for screen in cursor.fetchall():
            client['screens']['id'].append(screen['screen_id'])
            client['screens']['title'].append(screen['title'])
        cursor.close()
        return client

    def get_screen(self, screen_id):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute('SELECT title, text, label, is_array, next_screen_id FROM screen WHERE id=%s',
                       (screen_id,))
        screen = cursor.fetchone()
        screen['options'] = {'text': [], 'value': [], 'next_screen_id': []}
        cursor.execute('SELECT text, value, next_screen_id FROM screen_option WHERE screen_id=%s',
                       (screen_id,))
        for option in cursor.fetchall():
            screen['options']['text'].append(option['text'])
            screen['options']['value'].append(option['value'])
            screen['options']['next_screen_id'].append(option['next_screen_id'])
        cursor.close()
        return screen

    def put_response(self, client_id, data):
        cursor = self.db.cursor()
        cursor.execute('INSERT INTO response(client_id, data) VALUES(%s, %s)',
                       (client_id, data))
        response_id = cursor.lastrowid
        cursor.close()
        self.db.commit()
        return response_id

    def put_message(self, ticket_id, data):
        cursor = self.db.cursor()
        cursor.execute('INSERT INTO message(ticket_id, data) VALUES(%s, %s)',
                       (ticket_id, data))
        cursor.close()
        self.db.commit()

    def get_fcm_tokens(self,client_id):
        fcm_tokens = []
        cursor = self.db.cursor()
        cursor.execute('SELECT fcm_token FROM user WHERE client_id=%s',
                       (client_id,))
        for fcm_token, in cursor.fetchall():
            fcm_tokens.append(fcm_token)
        cursor.close()
        return fcm_tokens

