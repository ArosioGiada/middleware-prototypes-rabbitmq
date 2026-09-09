import pika
import json
import sys
import threading
import time

if len(sys.argv) < 4:
    print("Usage Windows: python chat_queue_version.py <username> <room> <port>")
    print("Usage Mac: python3 chat_queue_version.py <username> <room> <port>")
    sys.exit(1)

username = sys.argv[1]
room = sys.argv[2]
port = int(sys.argv[3])


def receive_messages():
    try:
        receive_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', port=port, heartbeat=600)
        )
        receive_channel = receive_connection.channel()

        receive_channel.queue_declare(queue=room)

        def callback(ch, method, properties, body):
            data = json.loads(body.decode())
            sender = data["sender"]
            message = data["message"]

            if sender != username:
                print(f"\n{sender}: {message}")

        receive_channel.basic_consume(
            queue=room,
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

        send_channel.queue_declare(queue=room)

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
                exchange='',
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