from flask import Flask, render_template, Response, url_for, request
import time


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/select_robot")
def select_robot():
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


if __name__ == '__main__':
    app.run(debug=True)