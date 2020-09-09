from flask import Flask, render_template, Response, url_for, request, send_file, abort, send_from_directory

import yaml
import time
import threading

from utils import is_url

import qi
from naoqi import ALProxy


app = Flask(__name__)

@app.route('/')
def index():
    try:
        global qi_session
        if qi_session is not None:
            print("Reconnect")
            global ip
            print(ip)
            return render_template("index.html", config=config, reconnect=True, reconnect_ip=ip)
    except NameError:
        return render_template('index.html', config=config, reconnect=False)

@app.route("/connect_robot")
def connect_robot():
    global ip
    ip = request.args.get('ip', type=str)
    port = 9559


    global qi_session
    qi_session = qi.Session()
    
    try:
        qi_session.connect(str("tcp://" + str(ip) + ":" + str(port)))
    except RuntimeError as msg:
        print("qi session connect error!:")
        print(msg)
    
    tts_srv = qi_session.service("ALTextToSpeech")
    tts_srv.setVolume(0.1)
    tts_srv.say("Connected")
    volume_lvl = tts_srv.getVolume()
    voice_pitch = tts_srv.getParameter("pitchShift")
    voice_pitch = round(voice_pitch, 3)

    al_srv = qi_session.service("ALAutonomousLife")
    autonomous_state = al_srv.getState()

    ba_srv = qi_session.service("ALBasicAwareness")
    engagement_state = ba_srv.getEngagementMode()
    ba_runnning = ba_srv.isRunning()

    ab_srv = qi_session.service("ALAutonomousBlinking")
    blinking_enabled = ab_srv.isEnabled()

    motion_srv = qi_session.service("ALMotion")
    orthogonal_collision = motion_srv.getOrthogonalSecurityDistance()
    orthogonal_collision = round(orthogonal_collision, 3)

    tangential_collision = motion_srv.getTangentialSecurityDistance()
    tangential_collision = round(tangential_collision, 3)

    body_breathing = motion_srv.getBreathEnabled("Body")
    legs_breathing = motion_srv.getBreathEnabled("Legs")
    arms_breathing = motion_srv.getBreathEnabled("Arms")
    head_breathing = motion_srv.getBreathEnabled("Head")

    return {
        "status": "ok",
        "ip": ip,
        "autonomous_state": autonomous_state,
        "engagement_state": engagement_state,
        "ba_is_running": ba_runnning,
        "blinking_enabled": blinking_enabled,
        "orthogonal_collision": orthogonal_collision,
        "tangential_collision": tangential_collision,
        "head_breathing": head_breathing,
        "arms_breathing": arms_breathing,
        "body_breathing": body_breathing,
        "legs_breathing": legs_breathing,
        "volume_lvl": volume_lvl,
        "voice_pitch": voice_pitch
    }

@app.route("/set_autonomous_state")
def set_autonomous_state():
    state = request.args.get('state', type=str)
    print(state)

    al_srv = qi_session.service("ALAutonomousLife")
    al_srv.setState(state)
    time.sleep(2)

    return {
       "status": "ok",
       "state": state 
    }

@app.route("/toggle_setting")
def toggle_setting():
    setting = request.args.get('setting', type=str)
    curr_state = request.args.get('curr_state', type=str)

    print(setting)
    print(curr_state)

    motion_srv = qi_session.service("ALMotion")
    ab_srv = qi_session.service("ALAutonomousBlinking")

    if setting == "blinking":
        if curr_state == "ON":
            ab_srv.setEnabled(False)
        else:
            ab_srv.setEnabled(True)
    elif setting == "head_breathing":
        if curr_state == "ON":
            motion_srv.setBreathEnabled("Head", False)
        else:
            motion_srv.setBreathEnabled("Head", True)
    elif setting == "arms_breathing":
        if curr_state == "ON":
            motion_srv.setBreathEnabled("Arms", False)
        else:
            motion_srv.setBreathEnabled("Arms", True)
    elif setting == "body_breathing":
        if curr_state == "ON":
            motion_srv.setBreathEnabled("Body", False)
        else:
            motion_srv.setBreathEnabled("Body", True)
    elif setting == "legs_breathing":
            if curr_state == "ON":
                motion_srv.setBreathEnabled("Legs", False)
            else:
                motion_srv.setBreathEnabled("Legs", True)

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

    tts = qi_session.service("ALTextToSpeech")
    tts.say(msg)

    return {
       "status": "ok",
       "text": msg,
    }

@app.route("/serve_audio/<path:filename>")
def serve_audio(filename):
    print(filename)
    return send_from_directory(config["audio_root_location"], filename)


@app.route("/play_audio")
def play_audio():
    # doesn't work :/
    # ap_srv = qi_session.service("ALAudioPlayer")
    # ap_srv.playWebStream("https://www2.cs.uic.edu/~i101/SoundFiles/CantinaBand60.wav", 0.1, 0.0)

    index = request.args.get('index', type=int)
    print(index)

    tablet_srv = qi_session.service("ALTabletService")
    tablet_srv.showWebview("http://130.239.183.189:5000/show_img_page/sound_playing.png")

    time.sleep(1)  # to ensure that tablet is ready, otherwise audio might not play...

    location = config["audio_files"][index]["location"]

    if not is_url(location):
        location = "http://130.239.183.189:5000/serve_audio/" + location
        print(location)


    tts_srv = qi_session.service("ALTextToSpeech")
    volume = tts_srv.getVolume()

    js_code = """
        var audio = new Audio('{}'); 
        audio.volume = {};
        audio.play();""".format(location, volume)


    tablet_srv.executeJS(js_code)
    time.sleep(60)  # TODO: dynamic length 
    tablet_srv.hideWebview()

    return {
       "status": "ok",
    }

@app.route("/show_img/<img_name>")
def show_img(img_name):
    tablet_srv = qi_session.service("ALTabletService")
    # very hacky, but this is the only way I got this to work... 
    # Think we have to do it this way, because we don't want the image to be rendered in the main browser, but dispatch it to pepper's tablet
    # TODO: get IP dynamicaly
    tablet_srv.showWebview("http://130.239.183.189:5000/show_img_page/" + img_name)

    # this works as well...:
    # js_code = """
    #    var audio = new Audio('https://www2.cs.uic.edu/~i101/SoundFiles/CantinaBand60.wav'); 
    #    audio.volume = 0.1;
    #    audio.play();"""

    # tablet_srv.executeJS(js_code)

    return {
       "status": "ok",
       "img_name": img_name
    }

@app.route("/show_img_page/<img_name>")
def show_img_page(img_name):
    img_path = "/static/imgs/" + img_name
    img_path = config["image_root_location"] + img_name
    print(img_path)
    return render_template("img_view.html", img_src=img_path)  # WORKS! 

@app.route("/clear_tablet")
def clear_tablet():
        tablet_srv = qi_session.service("ALTabletService")
        tablet_srv.hideWebview()

        return {
            "status": "cleaned tablet webview"
        }

@app.route("/set_engagement_state")
def set_engagement_state():
    state = request.args.get('state', type=str)
    print(state)

    ba_srv = qi_session.service("ALBasicAwareness")
    ba_srv.setEngagementMode(state)

    return {
       "status": "ok",
       "engagement_state": state 
    }

@app.route("/adjust_volume")
def adjust_volume():
    target = request.args.get('volume', type=float)
    target = target / 100.0  # slider range is 1 - 100, api wants 0 - 1 

    tts_srv = qi_session.service("ALTextToSpeech")
    tts_srv.setVolume(target)

    return {
        "status": "ok",
        "volume": target
    } 

@app.route("/exec_anim_speech")
def exec_anim_speech():
    index = request.args.get('index', type=int)
    print(index)

    annotated_text = config["animated_speech"][index]["string"]


    as_srv = qi_session.service("ALAnimatedSpeech")
    as_srv.say(annotated_text)

    return {
        "status": "ok",
        "annotated_text": annotated_text
    }

@app.route("/exec_gesture")
def exec_gesture():
    index = request.args.get('index', type=int)
    print(index)

    gesture = config["gestures"][index]["string"]

    ap_srv = qi_session.service("ALAnimationPlayer")
    ap_srv.run(gesture)

    return {
        "status": "ok",
        "gesture": gesture
    }



if __name__ == '__main__':

    global config
    with open("config.yaml", "r") as f:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        config = yaml.safe_load(f)
        print(config)

    app.run(host='0.0.0.0', debug=True)