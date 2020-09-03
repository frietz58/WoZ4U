from flask import Flask, render_template, Response, url_for, request


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/select_robot")
def select_robot():
    ip = request.args.get('ip', type=str)
    print(ip)

    # TODO: Connect to pepper

    return {
        "status": "ok",
        "ip": ip
        }

@app.route("/pepper_vision")
def pepper_vision():
    return render_template("pepper_vision.html")


if __name__ == '__main__':
    app.run(debug=True)