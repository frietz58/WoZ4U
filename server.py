from flask import Flask, render_template, Response, url_for


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/emotion_recognition")
def emotion_recognition():
    pass

@app.route("/pepper_vision")
def pepper_vision():
    return render_template("pepper_vision.html")


if __name__ == '__main__':
    app.run(debug=True)