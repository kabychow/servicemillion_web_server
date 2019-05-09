from helper.database import DB
from helper import queue, session, knowledge, nlp, fcm
from helper.router import *


''''''''''''''''''''''''''
' Initialize application '
''''''''''''''''''''''''''
# Reset all online session
_db = DB()
cursor = _db.con.cursor()
cursor.execute('UPDATE queue SET status=0 WHERE status=1')
cursor.close()

# Pre-cache knowledge for all clients
for client in DB().get_all_clients():
    knowledge.knowledges[client['id']] = knowledge.Knowledge(client['knowledge'])

app = Router(__name__)


''''''''''''''''''''''''''
' Real-time chat service '
''''''''''''''''''''''''''
@app.route('/chat/<client_id>', methods=['GET'])
def chat_form(client_id):
    return render_template('chat-form.html')


@app.route('/chat/<client_id>', methods=['POST'])
def chat(client_id):
    queue_id = queue.add(client_id, request.form['name'], request.form['email'], request.form['message'])
    fcm.send(client_id, title='New customer on queue', body='Tap to join chat')
    return render_template('chat.html', queue_id=queue_id)


''''''''''''''''''''
' Chat bot service '
''''''''''''''''''''
@app.route('/session/<api_key>/init')
def session_init(api_key):
    session_id = request.args['session_id']
    client = DB().get_client(api_key)
    if client is not None:
        sess = session.get(session_id)
        if sess is None:
            session_id, sess = session.add(client)
        return chatbot_encode(session_id=session_id, messages=sess.messages.get())


@app.route('/session/<session_id>/send')
def send(session_id):
    sess = session.get(session_id)
    data = request.args['message']
    response = []
    if sess is not None:
        sess.messages.add(data)
        action = sess.sequence.current('action')
        if isinstance(sess.sequence.current('type'), list):
            data = nlp.match_option(request.args['message'], sess.sequence.current('type'))
            if data is not None:
                if isinstance(action, list):
                    action = action[data]
                data = sess.sequence.current('type')[data]
        else:
            data = nlp.extract(request.args['message'], sess.sequence.current('type'))
        if data != '' and data is not None:
            sess.kv.add(sess.sequence.current('label'), data)
            sess.sequence.add(action)
        else:
            output = knowledge.get(sess.kv.get('$client_id')).get(request.args['message'])
            if output is not None:
                response.append(sess.messages.add({
                    'text': output,
                    'options': []
                }))
            else:
                response.append(sess.messages.add({
                    'text': "Hmm...",
                    'options': []
                }))
                response.append(sess.messages.add({
                    'text': 'I\'m not sure with that :(',
                    'options': [{'Contact customer support': 'http://localhost:5000/chat/' + str(sess.kv.get('$client_id'))}]
                }))
        if sess.sequence.current('action') is None:
            sess.kv.add('$tracking_id', DB().add_response(sess.kv.get('$client_id'), sess.kv.get()))
            fcm.send(sess.kv.get('$client_id'), title='New response received', body='Tap to view response')
        response.append(sess.messages.add({
            'text': sess.kv.extract(sess.sequence.current('text')),
            'options': sess.sequence.current('type') if isinstance(sess.sequence.current('type'), list) else []
        }))
        return chatbot_encode(messages=response)


''''''''''''''''''''''''''''''
' RestAPI service for mobile '
''''''''''''''''''''''''''''''
@app.route('/api/auth', methods=['POST'])
def auth():
    user = DB().get_user_by_email(request.form['email'])
    if user is not None and user['password'] == request.form['password']:
        return jsonify(api_key=user['api_key'])
    return jsonify(message='Incorrect username or password'), 401


@app.route('/api/fetch', methods=['GET'])
def fetch():
    user = DB().get_user(request.headers.get('authorization'))
    if user is not None:
        queues, tickets, responses = DB().get_data(user['client_id'])
        return jsonify(queues=queues, tickets=tickets, responses=responses)
    return jsonify(message='You\'re not logged in'), 403


@app.route('/api/me/fcm_token', methods=['POST'])
def fcm_token():
    user = DB().get_user(request.headers.get('authorization'))
    if user is not None:
        DB().set_user_fcm_token(user['id'], request.form['fcm_token'])
    return jsonify(message='You\'re not logged in'), 403
