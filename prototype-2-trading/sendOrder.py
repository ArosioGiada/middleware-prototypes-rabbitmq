import sys
import json
from datetime import datetime

import pika


ORDERS_QUEUE = "orders"
DEFAULT_STOCK = "XYZ"
ALLOWED_QUANTITY = 100
RABBITMQ_USERNAME = "guest"
RABBITMQ_PASSWORD = "guest"


def parse_endpoint(endpoint: str) -> tuple[str, int]:
    endpoint = endpoint.strip()
    if not endpoint:
        raise ValueError("endpoint cannot be empty")

    if ":" not in endpoint:
        raise ValueError("endpoint must be in the format host:port, e.g. localhost:5672")

    host, port_str = endpoint.split(":", 1)
    host = host.strip()
    if not host:
        raise ValueError("host cannot be empty")

    try:
        port = int(port_str)
    except ValueError as exc:
        raise ValueError("port must be an integer") from exc

    if port <= 0 or port > 65535:
        raise ValueError("port must be between 1 and 65535")

    return host, port


def validate_username(username: str) -> str:
    username = username.strip()
    if not username:
        raise ValueError("username cannot be empty")
    return username


def validate_side(side: str) -> str:
    side = side.strip().upper()
    if side not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")
    return side


def validate_quantity(quantity_str: str) -> int:
    try:
        quantity = int(quantity_str)
    except ValueError as exc:
        raise ValueError("quantity must be an integer") from exc

    if quantity != ALLOWED_QUANTITY:
        raise ValueError(f"quantity must be fixed at {ALLOWED_QUANTITY} for this assignment")

    return quantity


def validate_price(price_str: str) -> float:
    try:
        price = float(price_str)
    except ValueError as exc:
        raise ValueError("price must be a number") from exc

    if price <= 0:
        raise ValueError("price must be greater than 0")

    return price


def build_order(username: str, side: str, quantity: int, price: float) -> dict:
    return {
        "type": "order",
        "username": username,
        "stock": DEFAULT_STOCK,
        "side": side,
        "quantity": quantity,
        "price": price,
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }


def send_order(host: str, port: int, order: dict) -> None:
    credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=ORDERS_QUEUE)

    message = json.dumps(order)

    channel.basic_publish(
        exchange="",
        routing_key=ORDERS_QUEUE,
        body=message.encode("utf-8")
    )

    print("[x] Order sent successfully")
    print(message)

    connection.close()


def main() -> None:
    if len(sys.argv) != 6:
        print("Usage: python sendOrder.py <username> <host:port> <BUY|SELL> <quantity> <price>")
        print("Example: python sendOrder.py alice localhost:5672 BUY 100 12.5")
        sys.exit(1)

    try:
        username = validate_username(sys.argv[1])
        host, port = parse_endpoint(sys.argv[2])
        side = validate_side(sys.argv[3])
        quantity = validate_quantity(sys.argv[4])
        price = validate_price(sys.argv[5])

        order = build_order(username, side, quantity, price)
        send_order(host, port, order)

    except ValueError as err:
        print(f"Error: {err}")
        sys.exit(1)
    except pika.exceptions.AMQPConnectionError:
        print("Error: failed to connect to RabbitMQ. Please check the host, port, and server status.")
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected error: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()