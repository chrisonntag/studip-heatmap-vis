import os.path
import uuid
from functools import wraps
import simplejson as json
import traceback
import datetime
import bleach
from collections import defaultdict

from flask import Flask, Response
from flask import jsonify
from flask import request

import database
import studip


STATIC_DIR = '/static'

app = Flask(__name__, static_url_path=STATIC_DIR)
app.debug = True


def print_exceptions(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print('')
            print('------')
            print('API: exception')
            print(e)
            print(traceback.format_exc())
            print(request.url)
            print(request.data)
            print('------')
            raise
    return wrapped


def root_dir():
    return os.path.abspath(os.path.dirname(__file__)) + STATIC_DIR


def get_file(filename):
    try:
        src = os.path.join(root_dir(), filename)
        return open(src).read()
    except IOError as exc:
        return str(exc)


def get_error(msg):
    return jsonify({'result': 'ERROR', 'message': msg})


@app.route('/', methods=['GET'])
def root():
    content = get_file('index.html')
    return Response(content, mimetype="text/html")


# Serving static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_resource(path):
    mimetypes = {
        ".css": "text/css",
        ".html": "text/html",
        ".js": "application/javascript",
    }
    complete_path = os.path.join(root_dir(), path)
    ext = os.path.splitext(path)[1]
    mimetype = mimetypes.get(ext, "text/html")
    content = get_file(complete_path)
    return Response(content, mimetype=mimetype)


@app.route('/register', methods=['POST'])
@print_exceptions
def register():
    username = bleach.clean(request.form['username'])
    key = uuid.uuid4().hex
    if database.get_user(username) == None and studip.is_valid(username):
        database.register(username, key)
        return jsonify({'username': username, 'key': key})
    else:
        return get_error('Username not available in Stud.IP or already registered in this service.')


@app.route("/heatmap", methods=["GET"])
@print_exceptions
def get_data_heatmap():
    # TODO: Implement
    username = request.args.get('u', None)
    key = request.args.get('k', None)
    if username is not None and key is not None:
        return jsonify({'username': username, 'key': key})
    else:
        return get_error('No username and key.')


if __name__ == '__main__':
    app.run()

