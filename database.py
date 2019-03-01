import mysql.connector as mariadb

db = mariadb.connect(user='root', password='\'', database='superceed')


def get_client(client_id):
    cursor = db.cursor()
    cursor.execute('SELECT greetings, description FROM client WHERE id=%s', (client_id,))
    greetings, description = cursor.fetchone()
    cursor.execute('SELECT title, screen_id FROM client_screen WHERE client_id = %s', (client_id,))
    screens = {'title': [], 'screen_id': []}
    for title, screen_id in cursor.fetchall():
        screens['title'].append(title)
        screens['screen_id'].append(screen_id)
    cursor.close()
    return greetings, screens, description


def get_screen(screen_id):
    screen = {}
    cursor = db.cursor()
    cursor.execute('SELECT title, text, label, is_array, next_screen_id FROM screen WHERE id = %s', (screen_id,))
    screen['title'], screen['text'], screen['label'], screen['is_array'], screen['next_screen_id'] = cursor.fetchone()
    screen['options'] = {'text': [], 'value': [], 'next_screen_id': []}
    cursor.execute('SELECT text, value, next_screen_id FROM screen_option WHERE screen_id=%s', (screen_id,))
    for text, value, next_screen_id in cursor.fetchall():
        screen['options']['text'].append(text)
        screen['options']['value'].append(value)
        screen['options']['next_screen_id'].append(next_screen_id)
    cursor.close()
    return screen


def put_response(client_id, data):
    cursor = db.cursor()
    cursor.execute('INSERT INTO response(client_id, data) VALUES(%s, %s)', (client_id, data))
    cursor.close()
    db.commit()