import os.path
import uuid
from functools import wraps
import simplejson as json
import traceback
import datetime
import bleach
from collections import defaultdict

from flask import Flask, Response, render_template, make_response, url_for, redirect
from flask import jsonify
from flask import request

import database as db
import heatmap
from database import User, DayAction
import studip


STATIC_DIR = '/static'

app = Flask(__name__, static_url_path=STATIC_DIR, template_folder='static')
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


# Open database connection before requests and close them afterwards
@app.before_request
def before_request():
    db.DATABASE.connect()


@app.after_request
def after_request(response):
    db.DATABASE.close()
    return response


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

    if not db.user_exists(username, key) and studip.is_valid(username):
        points = studip.get_points(username)
        rank = studip.get_rank(username)

        try:
            db.create_user(username, key, points, rank)
        except db.IntegrityError:
            return get_error('Could not create user.')

        # return jsonify({'username': username, 'key': key, 'points': points, 'rank': rank})
        return redirect(url_for('show_user', username=username) + '?uuid=' + str(key))
    else:
        return get_error('Username not available in Stud.IP or already registered in this service.')


@app.route('/user/<username>', methods=['GET'])
@print_exceptions
def show_user(username=None):
    key = request.args.get('uuid', None)
    if username is not None and key is not None and db.user_exists(username, key):
        url = request.url_root[:-1] + url_for('get_data_heatmap')+'?user='+username+'&uuid='+str(key)
        return render_template('/overview.html', image_url=url)
    else:
        return get_error('Specify username and uuid.')


@app.route("/heatmap", methods=['GET'])
@print_exceptions
def get_data_heatmap():
    username = request.args.get('user', None)
    key = request.args.get('uuid', None)
    if db.user_exists(username, key):
        user = User.get(User.username == username, User.key == key)
        days = DayAction.select().where(DayAction.user == user)

        result = dict()
        for day in days:
            result[str(day.date)] = day.actions

        response=make_response(heatmap.generate_image(result).getvalue())
        response.headers['Content-Type'] = 'image/png'
        return response
        # return jsonify(result)
    else:
        return get_error('No username or wrong key.')


if __name__ == '__main__':
    app.run()

