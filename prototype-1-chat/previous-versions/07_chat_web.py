from flask import Flask, request, redirect, url_for, session, jsonify, render_template_string
import threading
import pika
import json
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "supersecretkey"

EXCHANGE_NAME = "chat_exchange"
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672

# Store messages per room
room_messages = defaultdict(list)

# Track active receivers per room
active_receivers = set()
receiver_lock = threading.Lock()


JOIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Join Chat</title>
</head>
<body>
    <h2>Join Chat Room</h2>
    <form method="post" action="/join">
        <label>Username:</label><br>
        <input type="text" name="username" required><br><br>

        <label>Room:</label><br>
        <input type="text" name="room" required><br><br>

        <button type="submit">Join Chat</button>
    </form>
</body>
</html>
"""

CHANGE_ROOM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Change Room</title>
</head>
<body>
    <h2>Change Room</h2>
    <p><strong>User:</strong> {{ username }}</p>

    <form method="post" action="/change-room">
        <label>New Room:</label><br>
        <input type="text" name="room" required><br><br>
        <button type="submit">Join New Room</button>
    </form>

    <br>
    <form method="get" action="/chat">
        <button type="submit">Back to Chat</button>
    </form>
</body>
</html>
"""

CHAT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Room</title>
    <script>
        async function fetchMessages() {
            const response = await fetch("/messages");
            const data = await response.json();

            const messagesDiv = document.getElementById("messages");
            messagesDiv.innerHTML = "";

            data.messages.forEach(msg => {
                const p = document.createElement("p");
                p.textContent = msg;
                messagesDiv.appendChild(p);
            });

            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        async function sendMessage(event) {
            event.preventDefault();

            const messageInput = document.getElementById("message");
            const message = messageInput.value.trim();

            if (!message) return;

            await fetch("/send", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: message })
            });

            messageInput.value = "";
            fetchMessages();
        }

        setInterval(fetchMessages, 1000);
        window.onload = fetchMessages;
    </script>
</head>
<body>
    <h2>Room: {{ room }}</h2>
    <p><strong>User:</strong> {{ username }}</p>

    <div id="messages" style="border:1px solid #ccc; height:300px; width:600px; overflow-y:scroll; padding:10px; margin-bottom:10px;">
    </div>

    <form onsubmit="sendMessage(event)">
        <input type="text" id="message" placeholder="Type a message" style="width:500px;" required>
        <button type="submit">Send</button>
    </form>

    <br>
    <form method="get" action="/change-room" style="display:inline;">
        <button type="submit">Change Room</button>
    </form>

    <form method="get" action="/logout" style="display:inline; margin-left:10px;">
        <button type="submit">Log Out</button>
    </form>
</body>
</html>
"""


def ensure_receiver(room):
    with receiver_lock:
        if room in active_receivers:
            return
        active_receivers.add(room)

    thread = threading.Thread(target=receive_messages, args=(room,), daemon=True)
    thread.start()


def receive_messages(room):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, heartbeat=600)
        )
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')

        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=queue_name,
            routing_key=room
        )

        def callback(ch, method, properties, body):
            data = json.loads(body.decode())
            sender = data["sender"]
            message = data["message"]
            room_messages[room].append(f"{sender}: {message}")

        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=True
        )

        channel.start_consuming()

    except Exception as e:
        room_messages[room].append(f"[Receive error] {e}")


@app.route("/")
def home():
    return render_template_string(JOIN_HTML)


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

    return render_template_string(CHAT_HTML, username=username, room=room)


@app.route("/send", methods=["POST"])
def send():
    username = session.get("username")
    room = session.get("room")

    if not username or not room:
        return jsonify({"status": "error", "message": "Not in a room"}), 400

    data = request.get_json()
    message_text = data.get("message", "").strip()

    if not message_text:
        return jsonify({"status": "error", "message": "Empty message"}), 400

    message = {
        "sender": username,
        "room": room,
        "message": message_text
    }

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT, heartbeat=600)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=room,
            body=json.dumps(message)
        )

        connection.close()

        return jsonify({"status": "ok"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/messages")
def messages():
    room = session.get("room")

    if not room:
        return jsonify({"messages": []})

    return jsonify({"messages": room_messages[room]})


@app.route("/change-room", methods=["GET", "POST"])
def change_room():
    username = session.get("username")

    if not username:
        return redirect(url_for("home"))

    if request.method == "POST":
        new_room = request.form.get("room", "").strip()

        if not new_room:
            return render_template_string(CHANGE_ROOM_HTML, username=username)

        session["room"] = new_room
        ensure_receiver(new_room)

        return redirect(url_for("chat"))

    return render_template_string(CHANGE_ROOM_HTML, username=username)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)