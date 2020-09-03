from flask import Flask, render_template, Response, url_for, request
import time


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/connect_robot")
def connect_robot():
    ip = request.args.get('ip', type=str)
    print(ip)

    # TODO: Connect to pepper
    time.sleep(2)

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


if __name__ == '__main__':
    app.run(debug=True)