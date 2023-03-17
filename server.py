from flask import Flask, render_template, Response, url_for, request, send_file, abort, send_from_directory, jsonify, \
    json

import yaml
import time
from datetime import datetime
import os
import matplotlib
from timeit import default_timer as timer
import jinja2
import sys
import signal
import requests

from utils import alImage_to_PIL
from utils import PIL_to_JPEG_BYTEARRAY
from utils import is_video
from utils import is_image
from utils import is_external_path
from utils import is_txt_file
import socket
import argparse
import logging
logger = logging.getLogger("mypackage.mymodule")  # or __name__ for current module
logger.setLevel(logging.ERROR)


from simple_sound_stream import SpeechRecognitionModule

import qi
import vision_definitions

from urlparse import unquote

app = Flask(__name__)

QI_SESSION = None

# helper for knowing what is on the tablet
TABLET_STATE = {
    "index": None,
    "video_or_website": False
}

global camera_tab_closed
camera_tab_closed = True

global camera_tab_timestamp
camera_tab_timestamp = 0

global touchdown_hist
touchdown_hist = []

global touchmove_hist
touchmove_hist = []

global touchmove_ind
touchmove_ind = 1

global latest_touchmove_used
latest_touchmove_used = 0

global SAVE_IMGS
SAVE_IMGS = False

global RECORD_AUDIO
RECORD_AUDIO = False

global motion_vector
motion_vector = [0, 0, 0]

# Tablet needs to know where server is running...
try:
    # weird linux hack to get ip if /etc/hosts maps hostname to 127.0.0.1
    # in that case, hostip would be 127.0.0.1 and pepper fails to reach server under that ip...
    # https://stackoverflow.com/questions/55296584/getting-127-0-1-1-instead-of-192-168-1-ip-ubuntu-python
    host_name = socket.gethostname()
    global HOST_IP
    HOST_IP = socket.gethostbyname(host_name + ".local")

except socket.gaierror:
    # this is the default case and works on max and windows...
    global HOST_IP
    HOST_IP = socket.gethostbyname(socket.gethostname())

FLASK_PORT = 5000
FLASK_HOME = "http://" + HOST_IP + ":" + str(FLASK_PORT) + "/"


@app.route('/')
def index():

    read_config()

    if QI_SESSION is not None and QI_SESSION.isConnected():  # if session already exists, fronted was just reloaded...
        global ip
        return render_template("index.html", config=config, reconnect_ip=ip)
    else:
        return render_template('index.html', config=config, reconnect_ip="")


@app.route("/connect_robot")
def connect_robot():
    """
    Connects to robot with given IP.
    """
    global ip
    ip = request.args.get('ip', type=str)
    global port
    port = 9559

    read_config()  # update the config in case it has been edited in the meantime, nice for developing ^

    global QI_SESSION

    if QI_SESSION is not None and QI_SESSION.isConnected():
        # connect btn has been pressed while robot was already connect --> it is the disconnedt btn...
        del QI_SESSION

        QI_SESSION = qi.Session()  # we make a new sess but don't connect it to anything --> essentially disconnect
        print("disconnecting interface by terminating session.")

        try:
            global SpeechRecognition
            SpeechRecognition.stop()
            del SpeechRecognition
        except (RuntimeError, NameError):
            # when camera tab is not open
            pass

        return {
            "status": "disconnected"
        }

    else:
        print "connecting interface to new robot session"

        # normal connect, we make a new session and connect to it
        try:
            # TODO doesn't solve the problem that session might still be trying to connect to invalid IP...
            print "attempting close and del session"
            QI_SESSION.close()
            del QI_SESSION
            time.sleep(1)
        except AttributeError:
            print "close attribute excaption pass..."
            # if the prev session is still trying to connect...
            pass

        QI_SESSION = None
        QI_SESSION = qi.Session()
        try:


            QI_SESSION.connect(str("tcp://" + str(ip) + ":" + str(port)))
        except RuntimeError as msg:
            print("qi session connect error!:")
            print(msg)

            QI_SESSION = None
            raise Exception("Couldn't connect session")

        print "past exception!"
        get_all_services()

        # almemory event subscribers
        # global tts_sub
        # tts_sub = mem_srv.subscriber("ALTextToSpeech/TextStarted")
        # tts_sub.signal.connect(tts_callback)
        tablet_srv.onTouchDownRatio.connect(touchDown_callback)  # on touch down, aka one "click"
        tablet_srv.onTouchMove.connect(touchMove_callback)  # finger slides on tablet
        tablet_srv.onTouchUp.connect(touchUp_callback)

        global vid_finished_signal
        vid_finished_signal = tablet_srv.videoFinished
        vid_finished_signal.connect(onVidEnd)

        tts_srv.setVolume(config["volume"])
        tts_srv.setParameter("pitchShift", config["voice_pitch"])
        tts_srv.setParameter("speed", config["voice_speed"])
        # tts_srv.say("Connected")

        # iterate over autonomous life configuration and set values...
        for key in config["autonomous_life_config"].keys():
            if config["autonomous_life_config"][key] == "":
                continue
            else:
                if key == "autonomous_state":
                    al_srv.setState(config["autonomous_life_config"][key])
                elif key == "tangential_collision":
                    motion_srv.setTangentialSecurityDistance(config["autonomous_life_config"][key])
                elif key == "orthogonal_collision":
                    motion_srv.setOrthogonalSecurityDistance(config["autonomous_life_config"][key])
                elif key == "blinking":
                    ab_srv.setEnabled(config["autonomous_life_config"][key])
                elif key == "engagement_mode":
                    ba_srv.setEngagementMode(config["autonomous_life_config"][key])
                elif key == "head_breathing":
                    motion_srv.setBreathEnabled("Head", config["autonomous_life_config"][key])
                elif key == "arms_breathing":
                    motion_srv.setBreathEnabled("Arms", config["autonomous_life_config"][key])
                elif key == "body_breathing":
                    motion_srv.setBreathEnabled("Body", config["autonomous_life_config"][key])
                elif key == "legs_breathing":
                    motion_srv.setBreathEnabled("Legs", config["autonomous_life_config"][key])
                elif key == "basic_awareness":
                    ba_srv.setEnabled(config["autonomous_life_config"][key])
                elif key == "listening_movement":
                    lm_srv.setEnabled(config["autonomous_life_config"][key])
                elif key == "speaking_movement":
                    sm_srv.setEnabled(config["autonomous_life_config"][key])

        # show default image if given
        show_default_img_or_hide()

        for color in config["colors"]:
            try:
                if color["is_default"]:
                    r = color["red"]
                    g = color["green"]
                    b = color["blue"]

                    led_srv.fadeRGB("FaceLeds", r, g, b, 0.5)

            except KeyError:  # only one of the elements should have the flag...
                pass

        return {
            "status": "ok",
            "ip": ip,
        }


def tts_callback(value):
    print("in tts callback")
    print(value)


def onVidEnd():
    TABLET_STATE["video_or_website"] = False
    pass


def touchDown_callback(x, y, msg):
    print(x, y, msg)
    # we append newest first, so that we can nicely iterate over list and fade color out...
    global touchdown_hist
    touchdown_hist.insert(0, (x, y))
    if len(touchdown_hist) > 5:
        touchdown_hist = touchdown_hist[:5]


def touchMove_callback(x_offset, y_offset):
    print("slide: ", touchmove_ind, x_offset, y_offset)
    # if this is a new "series" of touchmoves, create empty list of at current index
    global touchmove_hist
    global latest_touchmove_used

    if latest_touchmove_used != touchmove_ind:
        touchmove_hist.append([])
        latest_touchmove_used = touchmove_ind

    touchmove_hist[-1].append((x_offset / 1600, y_offset / 1080))


def touchUp_callback(x, y):
    print("Touchup!")
    global touchmove_ind
    touchmove_ind += 1

    global touchmove_hist
    touchmove_hist.append([])  # whenever we have a touchdown event, this might be followed by a finger slide...


def get_all_services():
    """
    Provides global references to all naoqi services used somewhere down the line
    """
    global tts_srv
    tts_srv = QI_SESSION.service("ALTextToSpeech")

    global al_srv
    al_srv = QI_SESSION.service("ALAutonomousLife")

    global ba_srv
    ba_srv = QI_SESSION.service("ALBasicAwareness")

    global ab_srv
    ab_srv = QI_SESSION.service("ALAutonomousBlinking")

    global motion_srv
    motion_srv = QI_SESSION.service("ALMotion")

    global video_srv
    video_srv = QI_SESSION.service("ALVideoDevice")

    global tablet_srv
    tablet_srv = QI_SESSION.service("ALTabletService")

    global as_srv
    as_srv = QI_SESSION.service("ALAnimatedSpeech")

    global ap_srv
    ap_srv = QI_SESSION.service("ALAnimationPlayer")

    global posture_srv
    posture_srv = QI_SESSION.service("ALRobotPosture")

    global ar_srv
    ar_srv = QI_SESSION.service("ALAudioRecorder")

    global ad_srv
    ad_srv = QI_SESSION.service("ALAudioDevice")

    global fd_srv
    fd_srv = QI_SESSION.service("ALFaceDetection")

    global mem_srv
    mem_srv = QI_SESSION.service("ALMemory")

    global lm_srv
    lm_srv = QI_SESSION.service("ALListeningMovement")

    global sm_srv
    sm_srv = QI_SESSION.service("ALSpeakingMovement")

    global audio_player
    audio_player = QI_SESSION.service("ALAudioPlayer")

    global led_srv
    led_srv = QI_SESSION.service("ALLeds")


@app.route("/querry_states")
def querry_states():
    """
    Querries all states that are easily accessable. EG: What autunomous state are we in or
    which seting is toggeled?
    @return: A dict with ids from the frontend, with the value being what that element should represent
    """
    try:
        # see if audio transmission is running even though camera tab is closed...
        try:
            now = timer()

            # this should be obsolete now, camera calls close method when closed... but having this here doesn't hurt,
            # so leaving it, just in case
            if now - camera_tab_timestamp > 3:  # if now keep alive ping within 5 seconds...
                if SpeechRecognition.isStarted:
                    print("Handling close camera tab!")
                    SpeechRecognition.stop()  # stop the audio transmission

                    # remove camera stream subscriber from video service
                    if video_srv.getSubscribers():
                        for subscriber in video_srv.getSubscribers():
                            if "CameraStream" in subscriber:  # name passed as argument on subscription
                                video_srv.unsubscribe(subscriber)

        except NameError:
            pass  # if SpeechRecognition module has never been started and doesn't exist...

        return {
            "#autonomous_states": al_srv.getState(),
            "#tangential_collision": round(motion_srv.getTangentialSecurityDistance(), 3) * 100,  # convert form m to
            "#orthogonal_collision": round(motion_srv.getOrthogonalSecurityDistance(), 3) * 100,  # cm for frontend
            "#toggle_btn_blinking": ab_srv.isEnabled(),
            "#toggle_btn_basic_awareness": ba_srv.isEnabled(),
            "#engagement_states": ba_srv.getEngagementMode(),
            "#toggle_btn_head_breathing": motion_srv.getBreathEnabled("Head"),
            "#toggle_btn_body_breathing": motion_srv.getBreathEnabled("Body"),
            "#toggle_btn_arms_breathing": motion_srv.getBreathEnabled("Arms"),
            "#toggle_btn_legs_breathing": motion_srv.getBreathEnabled("Legs"),
            "#volume_slider": tts_srv.getVolume(),
            "#voice_speed_input": tts_srv.getParameter("speed"),
            "#voice_pitch_input": tts_srv.getParameter("pitchShift"),
            "#motion_vector": [round(vel, 1) for vel in motion_srv.getRobotVelocity()],
            "#toggle_btn_listening": lm_srv.isEnabled(),
            "#toggle_btn_speaking": sm_srv.isEnabled(),
            "tablet_state": TABLET_STATE,
            "#querried_color": get_eye_colors(),
            "timestamp": timer()
        }
    except (NameError, RuntimeError):
        return {"STATE_QUERRY_ERR": "SESSION NOT AVAILABLE"}


@app.route("/set_autonomous_state")
def set_autonomous_state():
    """
    Sets the autunomous state
    """
    state = request.args.get('state', type=str)
    print(state)

    al_srv.setState(state)

    return {
        "status": "ok",
        "state": state
    }


@app.route("/set_engagement_mode")
def set_engagement_mode():
    """
    Sets the engagement mode
    """
    mode = request.args.get('mode', type=str)
    print(mode)

    ba_srv.setEngagementMode(mode)

    return {
        "status": "ok",
        "mode": mode
    }


@app.route("/say_text")
def say_text():
    msg = request.args.get('msg', type=str)

    tts_srv.say(msg)

    return {
        "status": "ok",
        "msg": msg
    }


@app.route("/toggle_setting")
def toggle_setting():
    setting = request.args.get('setting', type=str)
    print(setting)

    new_state = None
    if setting == "blinking":
        ab_srv.setEnabled(not ab_srv.isEnabled())
        new_state = ab_srv.isEnabled()

    elif setting == "head_breathing":
        motion_srv.setBreathEnabled("Head", not motion_srv.getBreathEnabled("Head"))
        new_state = motion_srv.getBreathEnabled("Head")

    elif setting == "arms_breathing":
        motion_srv.setBreathEnabled("Arms", not motion_srv.getBreathEnabled("Arms"))
        new_state = motion_srv.getBreathEnabled("Arms")

    elif setting == "body_breathing":
        motion_srv.setBreathEnabled("Body", not motion_srv.getBreathEnabled("Body"))
        new_state = motion_srv.getBreathEnabled("Body")

    elif setting == "legs_breathing":
        motion_srv.setBreathEnabled("Legs", not motion_srv.getBreathEnabled("Legs"))
        new_state = motion_srv.getBreathEnabled("Legs")

    elif setting == "basic_awareness":
        ba_srv.setEnabled(not ba_srv.isEnabled())
        new_state = ba_srv.isEnabled()

    elif setting == "listening":
        lm_srv.setEnabled(not lm_srv.isEnabled())
        new_state = lm_srv.isEnabled()

    elif setting == "speaking":
        sm_srv.setEnabled(not sm_srv.isEnabled())
        new_state = sm_srv.isEnabled()

    time.sleep(1)

    return {
        "status": "ok",
        "setting": setting,
        "new_state": new_state
    }


def show_default_img_or_hide():
    """
    Depending on whether a default image is given in the config, either shows that or resets the tablet to the default
    animation gif.
    """
    for enum_index, item in enumerate(config["tablet_items"]):
        if "is_default_img" in item.keys():
            url = FLASK_HOME + "show_img_page/" + str(enum_index)
            TABLET_STATE["index"] = enum_index

            tablet_srv.showWebview(url)

            return {
                "showing": "default image"
            }

    tablet_srv.hideWebview()
    TABLET_STATE["index"] = None

    return {
        "showing": "Pepper default gif, no default image found in config",
    }


@app.route("/serve_audio/<path:filename>")
def serve_audio(filename):
    print(filename)
    return send_from_directory(config["audio_root_location"], filename)


@app.route("/play_audio")
def play_audio():
    index = request.args.get('index', type=int)
    print(index)

    print("playing sound")

    location = config["audio_files"][index]["location"]

    # stored locally on pepper, here we can nicely use the ALAudio_player
    try:
        audio_file = audio_player.loadFile(location)
    except RuntimeError, e:
        return {
            "status": "error",
            "msg": "Couldn't load sound file '{}'. Make sure it is saved ON your pepper robot and check our README".format(location)
        }

    audio_player.setVolume(audio_file, tts_srv.getVolume())
    audio_player.play(audio_file)
    audio_player.unloadAllFiles()

    return {
        "status": "ok",
    }


@app.route("/stop_sound_play")
def stop_sound_play():
    audio_player.stopAll()
    audio_player.unloadAllFiles()

    return {
        "status": "stopped all sounds that were playing"
    }


@app.route("/show_tablet_item/<index>")
def show_tablet_item(index):
    app.logger.info('testing info log')
    item = config["tablet_items"][int(index)]["file_name"]


    if is_external_path(item) and not is_video(item) and not is_image(item):
        # tablet item is external website
        tablet_srv.enableWifi()
        tablet_srv.showWebview(item)
        TABLET_STATE["video_or_website"] = True

    elif is_video(item):
        if is_external_path(item):
            # externally hosted video
            video_src = item
        else:
            # video hosted locally, prepare "external" path foir tablet
            video_src = FLASK_HOME + config["tablet_root_location"] + item

        tablet_srv.enableWifi()
        tablet_srv.playVideo(video_src)
        TABLET_STATE["video_or_website"] = True

    else:
        tablet_srv.showWebview(FLASK_HOME + "show_img_page/" + index)

        TABLET_STATE["video_or_website"] = False

    TABLET_STATE["index"] = index

    return {
        "status": "ok",
        "item": item
    }

@app.route("/show_tablet_image")
def show_tablet_image():
    app.logger.info(request.args)
    url = requests.utils.unquote(request.args['name'])
    # tablet item is external website
    app.logger.info(url)
    tablet_srv.enableWifi()
    tablet_srv.showWebview(url)
    #tablet_srv.loadUrl("show_img_page/" + url)
    TABLET_STATE["video_or_website"] = True
    return {
        "status": "ok",
        "item": "haha"
    }


def get_tablet_img_from_index(index):
    img_obj = config["tablet_items"][int(index)]
    img_src = ""

    if is_external_path(img_obj["file_name"]):
        # if its externally hosted we don't have to do anything
        img_src = img_obj["file_name"]
    else:
        img_src = "/" + config["tablet_root_location"] + img_obj["file_name"]

    return img_src


@app.route("/show_img_page/<index>")
def show_img_page(index):
    img_src = get_tablet_img_from_index(index)
    return render_template("img_view.html", src=img_src, img_index=index)


@app.route("/clear_tablet")
def clear_tablet():
    tablet_srv.hideWebview()
    TABLET_STATE["index"] = None

    status = show_default_img_or_hide()
    status["msg"] = "cleaned tablet webview"

    return status


@app.route("/ping_curr_tablet_item")
def ping_curr_tablet_item():
    index = request.args.get('index', type=str)

    if not TABLET_STATE["video_or_website"]:
        TABLET_STATE["last_ping"] = timer()
        TABLET_STATE["index"] = index

        return {
            "set cur_tab_item": index
        }

    else:
        print("Got image tab ping, but ignored it because website or video is currently on tablet...")

        return {
            "ignered ping for cur_tab_item": index
        }




@app.route("/adjust_volume")
def adjust_volume():
    target = request.args.get('volume', type=float)
    target = target / 100.0  # slider range is 1 - 100, api wants 0 - 1 

    tts_srv.setVolume(target)
    currently_playing = audio_player.getLoadedFilesIds()
    for file in currently_playing:
        audio_player.setVolume(int(file), tts_srv.getVolume())

    return {
        "status": "ok",
        "volume": target,
        "currently playing audio files": currently_playing
    }


@app.route("/stop_tts")
def stop_tts():
    tts_srv.stopAll()
    tts_srv.say("")

    return {
        "status": "stopped TTS msg!"
    }


@app.route("/exec_anim_speech")
def exec_anim_speech():
    index = request.args.get('index', type=int)
    print(index)

    annotated_text = config["animated_speech"][index]["string"]

    if is_txt_file(annotated_text):
        with open(annotated_text, "r") as f:
            annotated_text = f.read()

    as_srv.say(annotated_text)

    return {
        "status": "ok",
        "annotated_text": annotated_text
    }


@app.route("/exec_gesture")
def exec_gesture():
    index = request.args.get('index', type=int)
    print(index)

    gesture = config["gestures"][index]["gesture"]

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
        value = value / 100.0  # for pitch shift we need to adjust the range... nice consistency in the naoqi api >.<
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


@app.route("/move_to")
def move_to():
    x = request.args.get("x", type=float)
    y = request.args.get("y", type=float)
    theta = request.args.get("theta", type=float)

    # Wake up robot
    # motion_service.wakeUp()

    # Send robot to Pose Init
    posture_srv.goToPosture("StandInit", 0.5)

    # set velocity
    motion_srv.moveTo(x, y, theta)

    return {
        "call": "move_to",
        "x": x,
        "y": y,
        "theta": theta
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

    stiffness = 0.5
    time = 1

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
    # see if there are any old video subscribers...
    try:
        if video_srv.getSubscribers():
            for subscriber in video_srv.getSubscribers():
                if "CameraStream" in subscriber:  # name passed as argument on subscription
                    video_srv.unsubscribe(subscriber)

    except (NameError, RuntimeError):
        # happens when camera tab is open when there is no server has been restarted?
        return render_template("camera.html")


    resolution = vision_definitions.kQVGA  # 320 * 240
    colorSpace = vision_definitions.kRGBColorSpace
    global imgClient
    imgClient = video_srv.subscribe("CameraStream", resolution, colorSpace, 30)

    global camera_tab_closed
    camera_tab_closed = False

    global camera_tab_timestamp
    camera_tab_timestamp = timer()

    global SpeechRecognition
    SpeechRecognition = SpeechRecognitionModule("SpeechRecognition", ip, port)
    SpeechRecognition.start()

    return render_template("camera.html")


@app.route("/close_camera_tab")
def close_camera_tab():
    try:
        global SpeechRecognition
        SpeechRecognition.stop()
        del SpeechRecognition

        if video_srv.getSubscribers():
            for subscriber in video_srv.getSubscribers():
                if "CameraStream" in subscriber:  # name passed as argument on subscription
                    video_srv.unsubscribe(subscriber)

    except (RuntimeError, NameError):
        # happens when cameratab is closed after naoqi session has been closed.
        pass



@app.route("/camera_tab_keep_alive")
def camera_tab_keep_alive():
    global camera_tab_timestamp
    camera_tab_timestamp = timer()
    connected = False
    try:
        if QI_SESSION is not None:

            # print(QI_SESSION.isConnected())
            # print QI_SESSION.__dict__
            if QI_SESSION.isConnected():
                connected = True
            else:
                connected = False
    except NameError:
        # when QI_SESSION is undefined, happens between connect and reconnect I think
        pass

    return {
        "set keep alive timestamp": camera_tab_timestamp,
        "connected": connected
    }


@app.route("/toggle_audio_mute")
def mute_audio():
    global SpeechRecognition
    if SpeechRecognition.isStarted:
        SpeechRecognition.stop()
    else:
        SpeechRecognition.start()

    return {
        "audio_running": SpeechRecognition.isStarted
    }



@app.route("/video_feed")
def video_feed():
    return Response(
        stream_generator(),
        mimetype='multipart/x-mixed-replace; boundary=frame')


def stream_generator():
    counter = 0
    while True:
        # frame = camera.get_frame()
        global imgClient
        try:
            alImage = video_srv.getImageRemote(imgClient)
            if alImage is not None:
                pil_img = alImage_to_PIL(alImage)

                # TODO: make image smaller? Might greatly decrease latency

                timestamp = datetime.now().strftime('%Y.%m.%d-%H:%M:%S.%f')[:-3]
                filename = timestamp + ".jpg"
                save_path = os.path.join(config["camera_save_dir"], filename)
                if not os.path.exists(config["camera_save_dir"]):
                    os.makedirs(config["camera_save_dir"])

                if SAVE_IMGS:
                    pil_img.save(save_path, "JPEG")

                jpeg_bytes = PIL_to_JPEG_BYTEARRAY(pil_img)

                counter += 1

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n\r\n')

            time.sleep(0.01)
        except (RuntimeError, NameError):
            # when session gets disconnected by camera tab is open
            pass


@app.route("/toggle_img_save")
def toggle_img_save():
    global SAVE_IMGS
    SAVE_IMGS = not SAVE_IMGS

    return {
        "SAVE_IMGS": SAVE_IMGS,
        "save_dir": config["camera_save_dir"]
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


@app.route("/set_led_intensity")
def set_led_intensity():
    group = request.args.get('led_group', type=str)
    intensity = request.args.get('intensity', type=float)
    intensity = intensity / 100.0
    print(group)
    print(intensity)
    led_srv.setIntensity(group, intensity)

    return {
        "staus": "updated led intensity",
        "LED group": group,
        "intensity": intensity
    }


@app.route("/set_led_color")
def set_led_color():
    group = "FaceLeds"

    color = request.args.get('color', type=str)

    for color_enum in config["colors"]:
        if color_enum["title"] == color:
            r = color_enum["red"]
            g = color_enum["green"]
            b = color_enum["blue"]

            print(r, g, b)
            print(group)

            led_srv.fadeRGB(group, r, g, b, 0.5)

            return {
                "staus": "updated led color",
                "color": color
            }


@app.route("/exec_eye_anim")
def exec_eye_anim():
    anim = request.args.get('anim', type=str)
    duration = request.args.get('secs', type=str)
    duration = float(duration)

    prev_color = get_eye_colors()
    # print(prev_color)

    if anim == "randomEyes":
        led_srv.randomEyes(duration)
    elif anim == "rasta":
        led_srv.rasta(duration)
    elif anim == "rotateEyes":
        color = request.args.get('color', type=str)

        for color_enum in config["colors"]:
            if color_enum["title"] == color:
                final_hex_int = matplotlib.colors.to_hex([color_enum["red"], color_enum["green"], color_enum["blue"]])
                # print(final_hex_int)
                final_hex_int = final_hex_int.replace("#", "0x")
                # print(final_hex_int)
                final_hex_int = int(final_hex_int, 16)
                # print(final_hex_int)

                round_time = 1.0
                led_srv.rotateEyes(final_hex_int, round_time, float(duration))

    # led_srv.fadeRGB("FaceLeds", 1.0, 1.0, 1.0, 0.5)
    led_srv.fadeRGB("FaceLeds", prev_color[0], prev_color[1], prev_color[2], 0.5)

    return {
        "status": "eye anim",
        "animation": anim
    }


def get_eye_colors():
    # just return the value of one of the Leds in one of the eyes...
    # this is BGR -.- the inconsistency in this API is unreal...
    bgr = led_srv.getIntensity("RightFaceLed1")
    rgb = [round(bgr[2], 2), round(bgr[1], 2), round(bgr[0], 2)]
    return rgb


@app.route("/tablet_drawer")
def tablet_drawer():
    return render_template('tablet_drawer.html')


@app.route("/get_touch_data")
def get_touch_data():

    global touchmove_hist
    filtered_touchmove_list = []
    # this one we must reverse here, because doing this before would be more cumbersome
    for sequence in reversed(touchmove_hist):
        if len(sequence) > 2:
            filtered_touchmove_list.append(sequence)

    if len(filtered_touchmove_list) > 5:
        filtered_touchmove_list = filtered_touchmove_list[:5]  # we keep the last 5 recent

    return {
        # we return the list in reverse order, so that we can put a nice fading color gradient on the older items...
        "touchdown_hist": touchdown_hist,
        "touchmove_hist": filtered_touchmove_list
    }


@app.route("/clear_touch_hist")
def cleat_touch_hist():
    global touchmove_hist
    touchmove_hist = []

    global touchdown_hist
    touchdown_hist = []

    global touchmove_ind
    touchmove_ind = 1

    global latest_touchmove_used
    latest_touchmove_used = 0

    return {
        "state": "reset all touch data to initial values"
    }


@app.route("/alive_test")
def alive_test():
    return {"status": "server is alive"}

def read_config(verbose=False):
    global config
    with open(CONFIG_FILE, "r") as f:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        config = yaml.safe_load(f)
        if verbose:
            print(config)


def pretty_print_shortcut(raw_string):
    """
    A custom Jinja 2 filter that formats the list.toString that we get in the frontent for the keyboard shortcut for
    the buttons.
    Is registered for Jinja in __main__
    :param raw_string: the list.toString() string form js
    :return: a beautified version of the string
    """
    pretty_string = str(raw_string)  # raw string is a list a this point...
    pretty_string = pretty_string.replace("[", "")
    pretty_string = pretty_string.replace("]", "")
    pretty_string = pretty_string.replace("'", "")
    pretty_string = pretty_string.replace(",", "")
    pretty_string = pretty_string.replace(" ", " + ")

    return pretty_string


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", dest="config", default="config.yaml", type=str, help="Which YAML configuration file to use. ")
    args = parser.parse_args()

    global CONFIG_FILE
    CONFIG_FILE = args.config

    read_config()

    # register custom filter for jinja2, so that we can use it in the frontend
    jinja2.filters.FILTERS['prettyshortcut'] = pretty_print_shortcut

    app.run(host='0.0.0.0', port=FLASK_PORT, debug=True)
