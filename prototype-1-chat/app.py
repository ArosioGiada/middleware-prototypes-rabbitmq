import os

from flask import Flask, request, redirect, url_for, session, jsonify, render_template
from rabbitmq_utils import ensure_receiver, send_message, room_messages

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")


@app.route("/")
def home():
    return render_template("join.html")


@app.route("/join", methods=["POST"])
def join():
    username = request.form.get("username", "").strip()
    room = request.form.get("room", "").strip()

    if not username or not room:
        return redirect(url_for("home"))

    session["username"] = username
    session["room"] = room

    ensure_receiver(room)

    return redirect(url_for("chat"))


@app.route("/chat")
def chat():
    username = session.get("username")
    room = session.get("room")

    if not username or not room:
        return redirect(url_for("home"))

    return render_template("chat.html", username=username, room=room)


@app.route("/send", methods=["POST"])
def send():
    username = session.get("username")
    room = session.get("room")

    if not username or not room:
        return jsonify({"status": "error"}), 400

    data = request.get_json()
    message_text = data.get("message", "").strip()

    if not message_text:
        return jsonify({"status": "error"}), 400

    send_message(username, room, message_text)

    return jsonify({"status": "ok"})


@app.route("/messages")
def messages():
    room = session.get("room")
    return jsonify({"messages": room_messages[room]})


@app.route("/change-room", methods=["GET", "POST"])
def change_room():
    username = session.get("username")

    if not username:
        return redirect(url_for("home"))

    if request.method == "POST":
        new_room = request.form.get("room", "").strip()

        if new_room:
            session["room"] = new_room
            ensure_receiver(new_room)
            return redirect(url_for("chat"))

    return render_template("change_room.html", username=username)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)