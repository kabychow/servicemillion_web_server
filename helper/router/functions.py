import json
from flask import request


def chatbot_encode(**kwargs):
    return '{callback}({data})'.format(callback=request.args.get('callback'), data=json.dumps(kwargs))
