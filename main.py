#!/usr/bin/python
import sqlite3
import requests
import base64

from bottle import route, post, get, run, request
from bottle import static_file

import json
from PIL import Image, ImageDraw


BASE_URL = 'http://32d0ef22.ngrok.com/'

db = sqlite3.connect('chess.db')

@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='static')

@post('/message')
def room():
    request_body = json.loads(request.body.read())
    user_message = request_body['item']['message']['message']
    user_room = str(request_body['item']['room']['id'])
    send_message('You said ' + user_message, user_room)

@post('/installable')
def install():
    install_configuration = request.body.read()
    install_configuration_json = json.loads(install_configuration)

    room_id = install_configuration_json['roomId']
    oauth_id = install_configuration_json['oauthId']
    oauth_secret = install_configuration_json['oauthSecret']

    db.execute('INSERT INTO rooms (room, oauthid, oauthsecret) VALUES (?, ?, ?)', (room_id, oauth_id, oauth_secret))
    db.execute('INSERT INTO games (room, state) VALUES (?, 1234)', (room_id,))

    db.commit()

@get('/game/<room_id>.png')
def render_game(room_id):
    size = (100,50)             # size of the image to create
    im = Image.new('RGB', size) # create the image
    draw = ImageDraw.Draw(im)   # create a drawing object that is
    # used to draw on the new image
    red = (255,0,0)    # color of our text
    text_pos = (10,10) # top-left position of our text
    text = "Hello World!" # text to draw
    # Now, we'll do the drawing:
    draw.text(text_pos, text, fill=red)

    image_path = 'dynamic-images/' + room_id + '.png'
    print 'Saving to ' + image_path
    im.save(image_path, 'PNG')

    return static_file(image_path, root='.')

def authorize(oauth_id, oauth_secret):
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
    print webhook_oauth_request.json()

    return webhook_oauth_request.json()['access_token']


def authorize_by_room(room_id):
    (_, oauth_id, oauth_secret) = db.execute('SELECT * FROM rooms WHERE room = ?', (room_id,)).fetchone()
    return authorize(oauth_id, oauth_secret)


def send_message(message, room_id):

    token = authorize_by_room(room_id)
    print 'Token : ' + str(token)
    message_params = {
        'message': '<img src="' + BASE_URL + 'game/' + room_id + '.png"></img>',
        'message_format': 'html',
        'color': 'green'
    }

    requests.post(
        'http://api.hipchat.com/v2/room/' + str(room_id) + '/notification?auth_token=' + token,
        json=message_params
    )

run(host='localhost', port=3421)