import json
from flask import Flask as Router, request, render_template, jsonify


def encode(**kwargs):
    return '{callback}({data})'.format(callback=request.args.get('callback'), data=json.dumps(kwargs))