#!/usr/bin/python
import sqlite3
import requests
import base64
import json
import re
import time

from bottle import route, post, get, run, request
from bottle import static_file

from view import render
from model import ChessGame, InvalidMove

BASE_URL = 'http://joshnelson.com.au/'

MOVE_COMMAND = '/chess move'
RESTART_COMMAND = '/chess restart'
VIEW_COMMAND = '/chess view'
HELP_COMMAND = '/chess help'

db = sqlite3.connect('chess.db')

@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='static')

@post('/message')
def room():
    request_body = json.loads(request.body.read())

    user_name = request_body['item']['message']['from']['name']
    user_message = request_body['item']['message']['message']
    room_id = str(request_body['item']['room']['id'])

    user_message = re.sub(r'//.*', '', user_message)  # strip comments from messages

    if user_message.startswith(MOVE_COMMAND):
        command = user_message.replace(MOVE_COMMAND + ' ', '')
        try:
            ChessGame(room_id).move(command)
            send_board_image(room_id)
            send_message(user_name + ' moved ' + command + '.<br>' + ChessGame(room_id).turn + ' to move.', room_id)
        except InvalidMove as e:
            send_message('Invalid move: ' + e.value, room_id)

    elif user_message.startswith(RESTART_COMMAND):
        ChessGame(room_id).restart()
        send_board_image(room_id)
        send_message(ChessGame(room_id).turn + ' to move.', room_id)

    elif user_message.startswith(VIEW_COMMAND):
        send_board_image(room_id)
        send_message(ChessGame(room_id).turn + ' to move.', room_id)

    elif user_message.startswith(HELP_COMMAND):
        send_message(
            '<ul>' +
                '<li><code>/chess help</code>: This command</li>' +
                '<li><code>/chess move a1 to h7</code>: Move the piece at a1 to h7</li>' +
                '<li><code>/chess restart</code>: Restart the game</li>' +
                '<li><code>/chess view</code>: View the current state of the game</li>' +
            '</ul>' +
            'Repository URL: <a href="https://github.com/cyberdash/hipchess">https://github.com/cyberdash/hipchess</a>'
        , room_id)

def send_board_image(room_id):
    send_message('<img src="' + BASE_URL + 'game/' + room_id + '.png"></img>', room_id)

@post('/installable')
def install():
    install_configuration = request.body.read()
    install_configuration_json = json.loads(install_configuration)

    room_id = install_configuration_json['roomId']
    oauth_id = install_configuration_json['oauthId']
    oauth_secret = install_configuration_json['oauthSecret']

    db.execute('INSERT INTO rooms (room, oauthid, oauthsecret) VALUES (?, ?, ?)', (room_id, oauth_id, oauth_secret))

    db.commit()

@get('/game/<room_id>.png')
def render_game(room_id):
    game = ChessGame(room_id)

    image_path = 'dynamic-images/' + room_id + '.png'

    print 'Saving to ' + image_path
    render(game, image_path)

    return static_file(image_path, root='.')

def send_message(message, room_id):

    token = authorize_by_room(room_id)
    print 'Sending message with token: ' + str(token)
    message_params = {
        'message': message,
        'message_format': 'html',
        'color': 'green'
    }

    requests.post(
        'http://api.hipchat.com/v2/room/' + str(room_id) + '/notification?auth_token=' + token,
        json=message_params
    )

token_cache = {}

def authorize(oauth_id, oauth_secret):

    if (oauth_id in token_cache) and token_cache[oauth_id]['expiry'] < time.time():
        return token_cache[oauth_id]['access_token']

    oauth_params = {
        'grant_type': 'client_credentials',
        'scope': 'admin_room send_notification'
    }

    oauth_headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + base64.b64encode(str(oauth_id) + ':' + str(oauth_secret))
    }
    webhook_oauth_request = requests.post(
        'http://api.hipchat.com/v2/oauth/token',
        params=oauth_params,
        headers=oauth_headers
    )
    access_token = webhook_oauth_request.json()['access_token']
    expires_in = webhook_oauth_request.json()['expires_in']

    token_cache[oauth_id] = {
        'expiry': time.time() + expires_in,
        'access_token': access_token
    }

    return access_token


def authorize_by_room(room_id):
    (_, oauth_id, oauth_secret) = db.execute('SELECT * FROM rooms WHERE room = ?', (room_id,)).fetchone()
    return authorize(oauth_id, oauth_secret)

run(host='0.0.0.0', port=5000)
