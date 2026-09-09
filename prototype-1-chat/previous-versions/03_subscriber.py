
import pika
import json
import sys

if len(sys.argv) < 2:
    print("Usage Windows: python 03_subscriber.py <room>")
    print("Usage Mac: python3 03_subscriber.py <room>")
    sys.exit(1)

room = sys.argv[1]

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)

channel = connection.channel()

channel.queue_declare(queue=room)

print(f"Waiting for messages in room '{room}'...")

def callback(ch, method, properties, body):
    data = json.loads(body.decode())
    print(f"{data['sender']}: {data['message']}")

channel.basic_consume(
    queue=room,
    on_message_callback=callback,
    auto_ack=True
)

channel.start_consuming()
