import json
from helper.database.helper.connection import Connection


class DB(Connection):

    def get_all_clients(self):
        cursor = self.con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM client_view')
        client = cursor.fetchall()
        cursor.close()
        return client

    def get_client(self, api_key):
        cursor = self.con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM client_view WHERE api_key=%s', (api_key,))
        client = cursor.fetchone()
        cursor.close()
        if client is not None:
            client['flow'] = json.loads(client['flow'])
        return client

    def get_all_users(self, client_id):
        cursor = self.con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user_view WHERE client_id=%s', (client_id,))
        users = cursor.fetchall()
        cursor.close()
        return users

    def get_user(self, api_key):
        cursor = self.con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user_view WHERE api_key=%s', (api_key,))
        user = cursor.fetchone()
        cursor.close()
        return user

    def get_user_by_email(self, email):
        cursor = self.con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user_view WHERE email=%s', (email,))
        user = cursor.fetchone()
        cursor.close()
        return user

    def set_user_fcm_token(self, user_id, fcm_token):
        cursor = self.con.cursor()
        cursor.execute('UPDATE user SET fcm_token=%s WHERE id=%s', (fcm_token, user_id))
        cursor.close()

    def add_queue(self, client_id, name, email, question):
        cursor = self.con.cursor()
        cursor.execute('INSERT INTO queue(client_id, name, email, question) VALUES (%s, %s, %s, %s)',
                       (client_id, name, email, question))
        queue_id = cursor.lastrowid
        cursor.close()
        return queue_id

    def get_queue(self, queue_id):
        cursor = self.con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM queue_view WHERE id=%s', (queue_id,))
        queue = cursor.fetchone()
        cursor.close()
        return queue

    def set_queue_status(self, queue_id, status):
        cursor = self.con.cursor()
        cursor.execute('UPDATE queue SET status=%s WHERE id=%s', (status, queue_id))
        cursor.close()

    def delete_queue(self, queue_id):
        cursor = self.con.cursor()
        cursor.execute('UPDATE queue SET is_deleted=1 WHERE id=%s', (queue_id,))
        cursor.close()

    def get_data(self, client_id):
        cursor = self.con.cursor(dictionary=True)
        cursor.execute('SELECT * FROM queue_view WHERE client_id=%s', (client_id,))
        queues = cursor.fetchall()
        cursor.execute('SELECT * FROM ticket_view WHERE client_id=%s', (client_id,))
        tickets = cursor.fetchall()
        cursor.execute('SELECT * FROM response_view WHERE client_id=%s', (client_id,))
        responses = []
        for response in cursor.fetchall():
            response['data'] = json.loads(response['data'])
            responses.append(response)
        cursor.close()
        return queues, tickets, responses

    def add_response(self, client_id, data):
        data = json.dumps(data)
        cursor = self.con.cursor()
        cursor.execute('INSERT INTO response(client_id, data) VALUES (%s, %s)', (client_id, data))
        response_id = cursor.lastrowid
        cursor.close()
        return response_id
