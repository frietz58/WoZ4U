from flask import Flask, render_template, Response, url_for, request, send_file, abort, send_from_directory, jsonify, json

import yaml
import time
import threading
from datetime import datetime
import os
import numpy as np

from utils import is_url
from utils import alImage_to_PIL
from utils import PIL_to_JPEG_BYTEARRAY

import qi
from naoqi import ALProxy
import vision_definitions

from urlparse import unquote

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

    get_all_services(qi_session)
    
    tts_srv.setVolume(0.1)
    tts_srv.say("Connected")
    volume_lvl = tts_srv.getVolume()
    voice_pitch = tts_srv.getParameter("pitchShift")
    voice_pitch = round(voice_pitch, 3)

    autonomous_state = al_srv.getState()

    engagement_state = ba_srv.getEngagementMode()
    ba_runnning = ba_srv.isRunning()

    blinking_enabled = ab_srv.isEnabled()

    orthogonal_collision = motion_srv.getOrthogonalSecurityDistance()
    orthogonal_collision = round(orthogonal_collision, 3)

    tangential_collision = motion_srv.getTangentialSecurityDistance()
    tangential_collision = round(tangential_collision, 3)

    body_breathing = motion_srv.getBreathEnabled("Body")
    legs_breathing = motion_srv.getBreathEnabled("Legs")
    arms_breathing = motion_srv.getBreathEnabled("Arms")
    head_breathing = motion_srv.getBreathEnabled("Head")

    vel_vec = motion_srv.getRobotVelocity()
    vel_vec = [round(vel, 3) for vel in vel_vec]

    # see if there are any old subscribers...
    if video_srv.getSubscribers():
        for subscriber in video_srv.getSubscribers():
            print("removing old video subscriber...")
            video_srv.unsubscribe(subscriber)

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
        "voice_pitch": voice_pitch,
        "velocity_vector": vel_vec
    }

def get_all_services(sess):
    """
    Provides global references to all naoqi services used somewhere down the line
    """
    global tts_srv 
    tts_srv  = qi_session.service("ALTextToSpeech")

    global al_srv
    al_srv = qi_session.service("ALAutonomousLife")

    global ba_srv
    ba_srv = qi_session.service("ALBasicAwareness")

    global ab_srv
    ab_srv = qi_session.service("ALAutonomousBlinking")

    global motion_srv
    motion_srv = qi_session.service("ALMotion")

    global video_srv
    video_srv = qi_session.service("ALVideoDevice")

    global tablet_srv
    tablet_srv = qi_session.service("ALTabletService")

    global as_srv
    as_srv = qi_session.service("ALAnimatedSpeech")

    global ap_srv
    ap_srv = qi_session.service("ALAnimationPlayer")

    global posture_srv
    posture_srv = qi_session.service("ALRobotPosture")

    global ar_srv
    ar_srv = qi_session.service("ALAudioRecorder")

    global ad_srv
    ad_srv = qi_session.service("ALAudioDevice")

    global fd_srv
    fd_srv = qi_session.service("ALFaceDetection")

    global mem_srv
    mem_srv = qi_session.service("ALMemory")

@app.route("/querry_states")
def querry_states():
    """
    Querries all states that are easily accessable. EG: What autunomous state are we in or
    which seting is toggeled?
    @return: A dict with ids from the frontend, with the value being what that element should represent
    """
    print("Querrying")
    try:
        return {
            "#autonomous_states": al_srv.getState(),
            "#tangential_collision": round(motion_srv.getTangentialSecurityDistance(), 3),
            "#orthogonal_collision": round(motion_srv.getOrthogonalSecurityDistance(), 3),
            "#toggle_btn_blinking": ab_srv.isEnabled(),
            "#toggle_btn_basic_awareness": ba_srv.isRunning(),
            "#engagement_states": ba_srv.getEngagementMode(),
            "#toggle_btn_head_breathing": motion_srv.getBreathEnabled("Head"),
            "#toggle_btn_body_breathing": motion_srv.getBreathEnabled("Body"),
            "#toggle_btn_arms_breathing": motion_srv.getBreathEnabled("Arms"),
            "#toggle_btn_legs_breathing": motion_srv.getBreathEnabled("Legs"),
            "#volume_slider": tts_srv.getVolume(),
            "#voice_speed_input": tts_srv.getParameter("speed"),
            "#voice_pitch_input": tts_srv.getParameter("pitchShift"),
            "#motion_vector": [round(vel, 3) for vel in motion_srv.getRobotVelocity()]
        }
    except NameError:
        return {"STATE_QUERRY_ERR": "SESSION NOT AVAILABLE"}

@app.route("/set_autonomous_state")
def set_autonomous_state():
    state = request.args.get('state', type=str)
    print(state)

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

    new_state = None
    if setting == "blinking":
        if curr_state == "ON":
            ab_srv.setEnabled(False)
        else:
            ab_srv.setEnabled(True)
        
        new_state = ab_srv.isEnabled()

    elif setting == "head_breathing":
        if curr_state == "ON":
            motion_srv.setBreathEnabled("Head", False)
        else:
            motion_srv.setBreathEnabled("Head", True)
        
        new_state = motion_srv.getBreathEnabled("Head")

    elif setting == "arms_breathing":
        if curr_state == "ON":
            motion_srv.setBreathEnabled("Arms", False)
        else:
            motion_srv.setBreathEnabled("Arms", True)
        
        new_state = motion_srv.getBreathEnabled("Arms")

    elif setting == "body_breathing":
        if curr_state == "ON":
            motion_srv.setBreathEnabled("Body", False)
        else:
            motion_srv.setBreathEnabled("Body", True)
        
        new_state = motion_srv.getBreathEnabled("Body")

    elif setting == "legs_breathing":
        if curr_state == "ON":
            motion_srv.setBreathEnabled("Legs", False)
        else:
            motion_srv.setBreathEnabled("Legs", True)

        new_state = motion_srv.getBreathEnabled("Legs")

    elif setting == "basic_awareness":
        if curr_state == "ON":
            ba_srv.setEnabled(False)
        else:
            ba_srv.setEnabled(True)
    
        new_state = ba_srv.isEnabled()

    # TODO: toggle setting
    time.sleep(2)

    return {
        "status": "ok",
        "setting": setting,
        "new_state": new_state
    }

@app.route("/say_text")
def say_text():
    msg = request.args.get('msg', type=str)
    print(msg)

    tts_srv.say(msg)

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

    tablet_srv.showWebview("http://130.239.183.189:5000/show_img_page/sound_playing.png")

    time.sleep(1)  # to ensure that tablet is ready, otherwise audio might not play...

    location = config["audio_files"][index]["location"]

    if not is_url(location):
        location = "http://130.239.183.189:5000/serve_audio/" + location
        print(location)


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
        tablet_srv.hideWebview()

        return {
            "status": "cleaned tablet webview"
        }

@app.route("/set_engagement_state")
def set_engagement_state():
    state = request.args.get('state', type=str)
    print(state)

    ba_srv.setEngagementMode(state)

    return {
       "status": "ok",
       "engagement_state": state 
    }

@app.route("/adjust_volume")
def adjust_volume():
    target = request.args.get('volume', type=float)
    target = target / 100.0  # slider range is 1 - 100, api wants 0 - 1 

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

    ap_srv.run(gesture)

    return {
        "status": "ok",
        "gesture": gesture
    }

@app.route("/exec_custom_gesture")
def exec_custom_gesture():
    string = request.args.get("string", type=str)
    print(string)

    gesture = unquote(string)
    print(gesture)

    ap_srv.run(gesture)

    return {
        "status": "ok",
        "gesture": gesture
    }

@app.route("/set_tts_param")
def set_tts_param():
    param = request.args.get("param", type=str)
    value = request.args.get("value", type=float)

    print(value)

    if param == "pitchShift":
        value = value // 100.0  # for pitch shift we need to adjust the range... nice consistency in the naoqi api >.<
        print(value)
        tts_srv.setParameter(param, value)
    else:
        tts_srv.setParameter(param, value)

    return {
            "status": "ok",
            "param": param,
            "value": value
        }

@app.route("/set_collision_radius")
def set_collision_radius():
    param = request.args.get("param", type=str)
    value = request.args.get("value", type=float)
    print(param)
    print(value)

    time.sleep(1)

    # get function dynamically from service object
    call = motion_srv.__getattribute__("set" + param + "SecurityDistance")
    call(value)

    return {
        "param": param,
        "value": value
    }
@app.route("/update_pepper_velocities")
def update_pepper_velocities():
        axis = request.args.get("axis", type=str)
        val = request.args.get("val", type=float)

        print(axis)
        print(val)

        # Disable all autonomous life features, they can interfere with our commands...
        al_srv.setState("solitary")
        al_srv.setAutonomousAbilityEnabled("All", False)

        # get current robot velocity
        x_vel, y_vel, theta_vel = motion_srv.getRobotVelocity()
        x_vel = round(x_vel, 3)
        y_vel = round(y_vel, 3)
        theta_vel = round(theta_vel, 3)

        # update velocity
        if axis == "x":
            x_vel += val
        elif axis == "theta":
            theta_vel += val

        stiffness = 0.1
        motion_srv.setStiffnesses("Body", stiffness)

        # set velocity
        motion_srv.move(x_vel, y_vel, theta_vel)

        return {
            "x_vel": x_vel,
            "y_vel": y_vel,
            "theta_vel": theta_vel,
            "target_axis": axis,
            "value": val
        }

@app.route("/stop_motion")
def stop_motion():
    motion_srv.stopMove()

    x_vel, y_vel, theta_vel = motion_srv.getRobotVelocity()
    x_vel = round(x_vel, 3)
    y_vel = round(y_vel, 3)
    theta_vel = round(theta_vel, 3)

    return {
        "status": "stopped move",
        "x_vel": x_vel,
        "y_vel": y_vel,
        "theta_vel": theta_vel
    }

@app.route("/resting_position")
def resting_position():
    motion_srv.stopMove()
    motion_srv.rest()

    return {
        "status": "entering resting position move"
    }

@app.route("/netural_stand_position")
def netural_stand_position():
    posture_srv.goToPosture("Stand", 0.5)

    return {
        "status": "entering 'Stand' posture"
    }


@app.route("/move_joint")
def move_joint():
    axis = request.args.get("axis", type=str)
    val = request.args.get("val", type=float)

    stiffness=0.5
    time=1

    if not motion_srv.robotIsWakeUp():
            motion_srv.wakeUp()
    
    motion_srv.setStiffnesses("Head", stiffness)

    motion_srv.angleInterpolation(
        [str(axis)],  # which axis
        [float(val)],  # amount of  movement
        [int(time)],  # time for movement
        False  # in absolute angles
        )

    if "Head" in axis:
        status = "moving head"
    elif "Hip" in axis:
        status = "moving hip"

    return {
        "status": status,
        "axis": axis,
        "val": val,
        "time": time,
        "stiffness": stiffness
    }

@app.route("/camera_view")    
def camera_view():
    # see if there are any old subscribers...
    if video_srv.getSubscribers():
        for subscriber in video_srv.getSubscribers():
            video_srv.unsubscribe(subscriber)


    resolution = vision_definitions.kQVGA  # 320 * 240
    colorSpace = vision_definitions.kRGBColorSpace
    global imgClient
    imgClient = video_srv.subscribe("_client", resolution, colorSpace, 5)

    return render_template("camera.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        stream_generator(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

def stream_generator():
    counter = 0
    try: 
        while True:
            # frame = camera.get_frame()
            global imgClient
            alImage = video_srv.getImageRemote(imgClient)
            if alImage is not None:
                pil_img = alImage_to_PIL(alImage)

                timestamp = datetime.now().strftime('%Y.%m.%d-%H:%M:%S.%f')[:-3]
                filename = timestamp + ".jpg"
                save_path = os.path.join(config["camera_save_dir"], filename)
                if SAVE_IMGS:
                    pil_img.save(save_path, "JPEG")

                jpeg_bytes = PIL_to_JPEG_BYTEARRAY(pil_img)

                counter += 1

                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n\r\n')

            time.sleep(0.01)
    except IOError:  # ideally this would catch the error when tab is closed, but it doesnt :/ TODO
        print("removing listener...")
        # see if there are any old subscribers...
        if video_srv.getSubscribers():
            for subscriber in video_srv.getSubscribers():
                video_srv.unsubscribe(subscriber)

@app.route("/toggle_img_save")
def toggle_img_save():
    global SAVE_IMGS
    SAVE_IMGS = not SAVE_IMGS

    return {
        "SAVE_IMGS": SAVE_IMGS
    }

@app.route("/record_audio_data")
def start_audio_recording():

    global RECORD_AUDIO
    RECORD_AUDIO = not RECORD_AUDIO    

    timestamp = datetime.now().strftime('%Y.%m.%d-%H:%M:%S.%f')[:-3]
    filename = timestamp + ".wav"
    save_path = os.path.join(config["audio_save_dir"], filename)

    if RECORD_AUDIO:
        ad_srv.enableEnergyComputation()
        ar_srv.startMicrophonesRecording(
            save_path,  
            "wav",
            16000,  # samplerate
            [1, 1, 1, 1]  # binary: which microphones do we want? [1, 1, 1, 1]  => all four... [0, 1, 0, 0] specific one
        )
    else:
        ar_srv.stopMicrophonesRecording()
        ad_srv.disableEnergyComputation()

    return {
        "now_recording_audio": RECORD_AUDIO,
        "pepper_save_dir": config["audio_save_dir"],
        "filename": filename
    }   

# TODO doesn't appear to detect faces even in perfect lighting (?)
@app.route("/face")
def face():
    return face_detect_stream()

def face_detect_stream():
    memValue = "FaceDetected"

    val = mem_srv.getData(memValue, 0)
    counter = 0

    while True:
        counter += 1
        time.sleep(0.5)

        result = {
                    "alpha": None,
                    "beta": None,
                    "width": None,
                    "height": None
                }

        val = mem_srv.getData(memValue, 0)
        print(val, counter)

        if(val and isinstance(val, list) and len(val) == 2):
            timeStamp = val[0]
            faceInfoArray = val[1]

            for faceInfo in faceInfoArray:
                faceShapeInfo = faceInfo[0]
                faceExtraInfo = faceInfo[1]

                result = {
                    "alpha": faceShapeInfo[1],
                    "beta": faceShapeInfo[2],
                    "width": faceShapeInfo[3],
                    "height": faceShapeInfo[4]
                }

        print(result)

                

if __name__ == '__main__':

    global config
    with open("config.yaml", "r") as f:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        config = yaml.safe_load(f)
        print(config)

    global SAVE_IMGS
    SAVE_IMGS = False
    RECORD_AUDIO = False

    app.run(host='0.0.0.0', debug=True)