import json

import pika


# RabbitMQ connection settings
HOST = "localhost"
PORT = 5672
USERNAME = "guest"
PASSWORD = "guest"
QUEUE_NAME = "trades"


def on_message(ch, method, properties, body):
    try:
        message = body.decode("utf-8")
        trade = json.loads(message)

        print("\n[x] Received trade")
        print(f"    stock      : {trade.get('stock')}")
        print(f"    buyer      : {trade.get('buyer')}")
        print(f"    seller     : {trade.get('seller')}")
        print(f"    quantity   : {trade.get('quantity')}")
        print(f"    price      : {trade.get('price')}")
        print(f"    buy price  : {trade.get('buy_order_price')}")
        print(f"    sell price : {trade.get('sell_order_price')}")
        print(f"    time       : {trade.get('timestamp')}")

    except json.JSONDecodeError:
        print(f"\n[!] Received invalid JSON: {body!r}")
    except Exception as e:
        print(f"\n[!] Error while processing trade: {e}")


def main():
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    parameters = pika.ConnectionParameters(
        host=HOST,
        port=PORT,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME)

    print(f"[*] Trade listener is running and listening on queue: {QUEUE_NAME}")
    print("[*] Press Ctrl+C to stop.\n")

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=on_message,
        auto_ack=True
    )

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Trade listener stopped.")