import json
from helper.database.connection import con


def get_all_knowledge():
    cursor = con.cursor()
    cursor.execute('SELECT api_key, knowledge FROM client')
    client = cursor.fetchall()
    cursor.close()
    return client


def get_client(api_key):
    cursor = con.cursor(dictionary=True)
    cursor.execute('SELECT flow, knowledge, api_key FROM client WHERE api_key=%s', (api_key,))
    client = cursor.fetchone()
    cursor.close()
    if client is not None:
        client['flow'] = json.loads(client['flow'])
    return client


def get_api_key(email, password):
    cursor = con.cursor(dictionary=True)
    cursor.execute('SELECT CONCAT(id, password) AS api_key FROM user WHERE email=%s AND password=PASSWORD(%s)',
                   (email, password))
    user = cursor.fetchone()
    if user is not None:
        return user['api_key']


def get_data(api_key):
    cursor = con.cursor(dictionary=True)
    cursor.execute('SELECT client_id FROM user WHERE CONCAT(id, password)=%s', (api_key,))
    user = cursor.fetchone()
    if user is not None:
        cursor.execute('SELECT id, name, email, question FROM queue WHERE client_id=%s', (user['client_id'],))
        queues = cursor.fetchall()
        cursor.execute('SELECT ticket.id, name, email, question FROM ticket '
                       'INNER JOIN queue ON ticket.queue_id = queue.id WHERE client_id=%s', (user['client_id'],))
        tickets = cursor.fetchall()
        cursor.execute('SELECT id, data FROM response WHERE client_id=%s ORDER by id DESC', (user['client_id'],))
        responses = []
        for response in cursor.fetchall():
            response['data'] = json.loads(response['data'])
            responses.append(response)
        return {'queues': queues, 'tickets': tickets, 'responses': responses}


def add_response(api_key, data):
    data = json.dumps(data)
    cursor = con.cursor()
    cursor.execute('INSERT INTO response(client_id, data) VALUES ((SELECT id FROM client WHERE api_key=%s), %s)',
                   (api_key, data))
    response_id = cursor.lastrowid
    cursor.close()
    return response_id


def add_queue(api_key, name, email, question):
    cursor = con.cursor()
    cursor.execute('INSERT INTO queue(client_id, name, email, question) VALUES '
                   '((SELECT id FROM client WHERE api_key=%s), %s, %s, %s)', (api_key, name, email, question))
    queue_id = cursor.lastrowid
    cursor.close()
    return queue_id
