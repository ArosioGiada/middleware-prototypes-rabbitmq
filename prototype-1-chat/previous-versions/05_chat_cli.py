import pika
import json
import sys
import threading
import time

if len(sys.argv) < 4:
    print("Usage Windows: python chat.py <username> <room> <port>")
    print("Usage Mac: python3 chat.py <username> <room> <port>")
    sys.exit(1)

username = sys.argv[1]
room = sys.argv[2]
port = int(sys.argv[3])

EXCHANGE_NAME = "chat_exchange"


def receive_messages():
    try:
        receive_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', port=port, heartbeat=600)
        )
        receive_channel = receive_connection.channel()

        # Declare topic exchange
        receive_channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type='topic'
        )

        # Create a temporary queue for this user
        result = receive_channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        # Bind queue to the selected room
        receive_channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=queue_name,
            routing_key=room
        )

        def callback(ch, method, properties, body):
            data = json.loads(body.decode())
            sender = data["sender"]
            message = data["message"]

            if sender != username:
                print(f"\n{sender}: {message}")

        receive_channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=True
        )

        receive_channel.start_consuming()

    except Exception as e:
        print(f"\n[Receive error] {e}")


def send_messages():
    try:
        send_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', port=port, heartbeat=600)
        )
        send_channel = send_connection.channel()

        # Declare topic exchange
        send_channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type='topic'
        )

        while True:
            message_text = input()

            if message_text.strip() == "":
                continue

            message = {
                "sender": username,
                "room": room,
                "message": message_text
            }

            send_channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=room,
                body=json.dumps(message)
            )

    except KeyboardInterrupt:
        print("\nExiting chat...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[Send error] {e}")
        sys.exit(1)


print(f"[Connected to room '{room}' as {username}]")
print("Type messages. Press Ctrl+C to exit.\n")

receive_thread = threading.Thread(target=receive_messages, daemon=True)
receive_thread.start()

time.sleep(1)

send_messages()