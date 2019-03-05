import mysql.connector as mariadb

db = mariadb.connect(user='root', password='root', database='superceed')


def get_client(client_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT id, greetings, description FROM client WHERE id=%s', (client_id,))
    client = cursor.fetchone()
    client['screens'] = {'id': [], 'title': []}
    cursor.execute('SELECT title, screen_id FROM client_screen WHERE client_id=%s', (client_id,))
    for screen in cursor.fetchall():
        client['screens']['id'].append(screen['screen_id'])
        client['screens']['title'].append(screen['title'])
    cursor.close()
    return client


def get_screen(screen_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT title, text, label, is_array, next_screen_id FROM screen WHERE id = %s', (screen_id,))
    screen = cursor.fetchone()
    screen['options'] = {'text': [], 'value': [], 'next_screen_id': []}
    cursor.execute('SELECT text, value, next_screen_id FROM screen_option WHERE screen_id=%s', (screen_id,))
    for option in cursor.fetchall():
        screen['options']['text'].append(option['text'])
        screen['options']['value'].append(option['value'])
        screen['options']['next_screen_id'].append(option['next_screen_id'])
    screen['is_last'] = screen['next_screen_id'] is None and len(screen['options']['next_screen_id']) == 0
    cursor.close()
    return screen


def put_response(client_id, data):
    cursor = db.cursor()
    cursor.execute('INSERT INTO response(client_id, data) VALUES(%s, %s)', (client_id, data))
    cursor.close()
    db.commit()
