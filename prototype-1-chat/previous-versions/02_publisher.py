import pika
import json
import sys

if len(sys.argv) < 3:
    print("Usage Windows: python 02_publisher.py <username> <room>")
    print("Usage Mac: python3 02_publisher.py <username> <room>")
    sys.exit(1)

username = sys.argv[1]
room = sys.argv[2]

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)

channel = connection.channel()

channel.queue_declare(queue=room)

print(f"Connected as {username} in room '{room}'")
print("Type messages. Press Ctrl+C to exit.")

while True:
    message_text = input()

    message = {
        "sender": username,
        "room": room,
        "message": message_text
    }

    channel.basic_publish(
        exchange='',
        routing_key=room,
        body=json.dumps(message)
    )