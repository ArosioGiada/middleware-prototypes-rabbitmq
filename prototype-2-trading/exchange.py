import sys
import json
from datetime import datetime

import pika


ORDERS_QUEUE = "orders"
TRADES_QUEUE = "trades"
DEFAULT_STOCK = "XYZ"
ALLOWED_QUANTITY = 100
RABBITMQ_USERNAME = "guest"
RABBITMQ_PASSWORD = "guest"

buy_orders = []
sell_orders = []


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


def validate_order(order: dict) -> dict:
    required_fields = ["type", "username", "stock", "side", "quantity", "price", "timestamp"]
    for field in required_fields:
        if field not in order:
            raise ValueError(f"missing required field: {field}")

    if order["type"] != "order":
        raise ValueError("invalid type field")

    if not isinstance(order["username"], str) or not order["username"].strip():
        raise ValueError("invalid username")

    if order["stock"] != DEFAULT_STOCK:
        raise ValueError(f"invalid stock; expected {DEFAULT_STOCK}")

    if order["side"] not in {"BUY", "SELL"}:
        raise ValueError("invalid side; expected BUY or SELL")

    if order["quantity"] != ALLOWED_QUANTITY:
        raise ValueError(f"invalid quantity; expected {ALLOWED_QUANTITY}")

    try:
        order["price"] = float(order["price"])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid price") from exc

    if order["price"] <= 0:
        raise ValueError("price must be greater than 0")

    return order


def publish_trade(channel, trade: dict) -> None:
    message = json.dumps(trade)
    channel.basic_publish(
        exchange="",
        routing_key=TRADES_QUEUE,
        body=message.encode("utf-8")
    )
    print("\n[TRADE PUBLISHED]")
    print(message)


def create_trade(buy_order: dict, sell_order: dict) -> dict:
    return {
        "type": "trade",
        "stock": DEFAULT_STOCK,
        "buyer": buy_order["username"],
        "seller": sell_order["username"],
        "quantity": ALLOWED_QUANTITY,
        "price": sell_order["price"],
        "buy_order_price": buy_order["price"],
        "sell_order_price": sell_order["price"],
        "timestamp": datetime.now().isoformat(timespec="seconds")
    }


def sort_order_books() -> None:
    buy_orders.sort(key=lambda order: (-order["price"], order["timestamp"]))
    sell_orders.sort(key=lambda order: (order["price"], order["timestamp"]))


def print_order_book() -> None:
    print("\n--- ORDER BOOK ---")

    print("BUY ORDERS:")
    if buy_orders:
        for order in buy_orders:
            print(f"  {order['username']} BUY {order['quantity']} {order['stock']} @ {order['price']}")
    else:
        print("  (empty)")

    print("SELL ORDERS:")
    if sell_orders:
        for order in sell_orders:
            print(f"  {order['username']} SELL {order['quantity']} {order['stock']} @ {order['price']}")
    else:
        print("  (empty)")

    print("------------------\n")


def try_match_order(channel, incoming_order: dict) -> None:
    side = incoming_order["side"]

    if side == "BUY":
        sort_order_books()

        if sell_orders and sell_orders[0]["price"] <= incoming_order["price"]:
            matched_sell = sell_orders.pop(0)
            trade = create_trade(incoming_order, matched_sell)

            print("\n[MATCH FOUND]")
            print(
                f"BUY {incoming_order['username']} @ {incoming_order['price']} "
                f"matched with SELL {matched_sell['username']} @ {matched_sell['price']}"
            )

            publish_trade(channel, trade)
            print_order_book()
            return

        buy_orders.append(incoming_order)
        sort_order_books()

        print("\n[NO MATCH] Added BUY order to order book.")
        print_order_book()

    elif side == "SELL":
        sort_order_books()

        if buy_orders and buy_orders[0]["price"] >= incoming_order["price"]:
            matched_buy = buy_orders.pop(0)
            trade = create_trade(matched_buy, incoming_order)

            print("\n[MATCH FOUND]")
            print(
                f"SELL {incoming_order['username']} @ {incoming_order['price']} "
                f"matched with BUY {matched_buy['username']} @ {matched_buy['price']}"
            )

            publish_trade(channel, trade)
            print_order_book()
            return

        sell_orders.append(incoming_order)
        sort_order_books()

        print("\n[NO MATCH] Added SELL order to order book.")
        print_order_book()

    else:
        print(f"[!] Unknown side: {side}")


def on_message(ch, method, properties, body):
    try:
        message = body.decode("utf-8")
        order = json.loads(message)
        order = validate_order(order)

        print("\n[x] Received order")
        print(f"    username : {order['username']}")
        print(f"    stock    : {order['stock']}")
        print(f"    side     : {order['side']}")
        print(f"    quantity : {order['quantity']}")
        print(f"    price    : {order['price']}")
        print(f"    time     : {order['timestamp']}")

        try_match_order(ch, order)

    except json.JSONDecodeError:
        print(f"\n[!] Received invalid JSON: {body!r}")
    except ValueError as err:
        print(f"\n[!] Invalid order rejected: {err}")
    except Exception as err:
        print(f"\n[!] Error while processing message: {err}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python exchange.py <host:port>")
        print("Example: python exchange.py localhost:5672")
        sys.exit(1)

    try:
        host, port = parse_endpoint(sys.argv[1])

        credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue=ORDERS_QUEUE)
        channel.queue_declare(queue=TRADES_QUEUE)

        print(f"[*] Exchange is running and listening on queue: {ORDERS_QUEUE}")
        print(f"[*] Connected to RabbitMQ at {host}:{port}")
        print("[*] Press Ctrl+C to stop.\n")

        channel.basic_consume(
            queue=ORDERS_QUEUE,
            on_message_callback=on_message,
            auto_ack=True
        )

        channel.start_consuming()

    except ValueError as err:
        print(f"Error: {err}")
        sys.exit(1)
    except pika.exceptions.AMQPConnectionError:
        print("Error: failed to connect to RabbitMQ. Please check the host, port, and server status.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Exchange stopped.")
        sys.exit(0)
    except Exception as err:
        print(f"Unexpected error: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()