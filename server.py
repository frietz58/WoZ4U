from flask import Flask, render_template, Response, url_for, request
import time

import qi
from naoqi import ALProxy


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def get_all_states():

    pass

@app.route("/connect_robot")
def connect_robot():
    ip = request.args.get('ip', type=str)
    port = 9559
    print(ip)

    global session
    session = qi.Session()
    
    try:
        session.connect(str("tcp://" + str(ip) + ":" + str(port)))
    except RuntimeError, e:
        print e

    tts = session.service("ALTextToSpeech")
    tts.setVolume(0.02)
    tts.say("Connected")

    return {
        "status": "ok",
        "ip": ip
    }

@app.route("/set_autonomous_state")
def set_autonomous_state():
    state = request.args.get('state', type=str)
    print(state)

    # TODO: set State
    time.sleep(2)

    return {
       "status": "ok",
       "state": state 
    }

@app.route("/toggle_setting")
def toggle_setting():
    setting = request.args.get('setting', type=str)
    print(setting)

    # TODO: toggle setting
    time.sleep(2)

    return {
       "status": "ok",
       "setting": setting,
        # TODO: return state
    }

@app.route("/say_text")
def say_text():
    msg = request.args.get('msg', type=str)
    print(msg)

    # TODO: Say the text
    time.sleep(2)

    return {
       "status": "ok",
       "text": msg,
    }

@app.route("/say_predefined_text")
def say_predefined_text():
    index = request.args.get('index', type=str)
    print(index)

    # TODO: Read the text from file
    msg = "some predefined text"

    # TODO: Say the text
    time.sleep(2)

    return {
       "status": "ok",
       "index": index, 
       "text": msg,
    }

@app.route("/play_audio")
def play_audio():
    index = request.args.get('index', type=str)
    print(index)

    # TODO: get audio file path
    path = "some/path"

    # TODO: Play the audio
    time.sleep(2)

    return {
       "status": "ok",
       "index": index, 
       "audio_file": path,
    }

@app.route("/show_img")
def show_img():
    index = request.args.get('index', type=str)
    print(index)

    # TODO: get img file path
    path = "some/img/path"

    # TODO: show the image on peppers tablet

    return {
        # TODO: Return the prev index so that we can reset the button
       "status": "ok",
       "index": index, 
       "image": path,
    }


if __name__ == '__main__':
    app.run(debug=True)