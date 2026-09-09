import threading
import pika
import json
from collections import defaultdict

EXCHANGE_NAME = "chat_exchange"
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672

room_messages = defaultdict(list)

active_receivers = set()
receiver_lock = threading.Lock()


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


def send_message(username, room, message_text):
    message = {
        "sender": username,
        "room": room,
        "message": message_text
    }

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