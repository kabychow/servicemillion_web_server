from helper import queue, database, session, knowledge, nlp
from helper.router import *

app = Router(__name__)


''''''''''''''''''''''''''
' Real-time chat service '
''''''''''''''''''''''''''
@app.route('/chat/<api_key>', methods=['GET'])
def chat_form(api_key):
    return render_template('chat-form.html', api_key=api_key)


@app.route('/chat/<api_key>', methods=['POST'])
def chat(api_key):
    queue_id = queue.add(api_key, request.form['name'], request.form['email'], request.form['message'])
    return render_template('chat.html', queue_id=queue_id)


''''''''''''''''''''
' Chat bot service '
''''''''''''''''''''
@app.route('/session/<api_key>/init')
def session_init(api_key):
    session_id = request.args['session_id']
    client = database.get_client(api_key)
    if client is not None:
        sess = session.get(session_id)
        if sess is None:
            session_id, sess = session.add(client)
        return encode(session_id=session_id, messages=sess.messages.get())


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
            output = knowledge.get(sess.kv.get('$api_key'), request.args['message'])
            if output is not None:
                response.append(sess.messages.add({
                    'text': output,
                    'options': []
                }))
            else:
                response.append(sess.messages.add({
                    'text': "I'm not sure with that :(",
                    'options': []
                }))
                response.append(sess.messages.add({
                    'text': "Do you want to contact customer support?",
                    'options': [{'Yes': 'http://localhost:5000/chat/' + sess.kv.get('$api_key')}, 'No']
                }))
        if sess.sequence.current('action') is None:
            sess.kv.add('$tracking_id', database.add_response(sess.kv.get('$api_key'), sess.kv.get()))
        response.append(sess.messages.add({
            'text': sess.kv.extract(sess.sequence.current('text')),
            'options': sess.sequence.current('type') if isinstance(sess.sequence.current('type'), list) else []
        }))
        return encode(messages=response)


''''''''''''''''''''''''''''''
' RestAPI service for mobile '
''''''''''''''''''''''''''''''
@app.route('/api/auth', methods=['POST'])
def auth():
    api_key = database.get_api_key(request.form['email'], request.form['password'])
    if api_key is not None:
        return jsonify(api_key=api_key)
    return jsonify(message='Incorrect username or password'), 401


@app.route('/api/fetch', methods=['GET'])
def fetch():
    data = database.get_data(request.headers.get('authorization'))
    if data is not None:
        return jsonify(data)
    return jsonify(message='You\'re not logged in'), 403
