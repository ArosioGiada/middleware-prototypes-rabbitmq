# Prototype 2 — Trading System

A simplified single-stock exchange simulation: traders submit buy/sell orders for one stock (**XYZ Corp**), an exchange service matches compatible orders against each other, and completed trades are published for anyone listening — including a live GUI dashboard.

## How it works

Two RabbitMQ queues drive the whole system: `orders` and `trades`. Traders and the exchange never talk to each other directly — every interaction goes through these two queues.

- **`sendOrder.py`** is a fire-and-forget CLI: it validates the order (username, side, quantity, price), publishes it to the `orders` queue, and exits immediately.
- **`exchange.py`** is the long-running matching engine. It subscribes to `orders`, keeps an in-memory order book (separate lists for buy and sell orders), and on every incoming order:
  - sorts the order book by price-time priority (best price first, oldest first as tiebreaker),
  - checks whether there's a compatible opposite-side order (a buyer willing to pay at least what a seller is asking),
  - if so, matches them, removes the matched order from the book, and publishes the trade to the `trades` queue,
  - otherwise, adds the incoming order to the book and waits.
- **`trade_listener.py`** and **`trade_gui.py`** are two independent consumers of the `trades` queue — a terminal printout and a graphical dashboard — demonstrating that any number of services can observe the same trade stream without affecting the exchange or each other.

## Stack

Python, [pika](https://pika.readthedocs.io/) (RabbitMQ client), Tkinter (GUI).

## Running it locally

Requirements: Python 3.9+, Docker (to run RabbitMQ), `pika` (see `requirements.txt`).

Start RabbitMQ:
```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
(Management UI at `http://localhost:15672`.)

Then, in separate terminals:
```bash
# 1. Start the exchange
python exchange.py localhost:5672

# 2. Start the trade listener (terminal output)
python trade_listener.py

# 3. Start the GUI dashboard
python trade_gui.py localhost:5672

# 4. Send some orders
python sendOrder.py bob localhost:5672 SELL 100 11.8
python sendOrder.py alice localhost:5672 BUY 100 12.5
```
The BUY and SELL orders above are priced to match, so you should immediately see a completed trade in both the terminal listener and the GUI.

## Known limitations

- **Single stock, fixed quantity.** The brief scoped this to one stock (XYZ Corp) and a fixed order size of 100 shares — both are hardcoded rather than configurable.
- **In-memory order book.** State is lost if the exchange process restarts; there's no persistence layer.
- **The dashboard UI includes some static/decorative elements** — the market tabs, sidebar categories, "Deposit Funds" button, volume figures, and order book depth chart — added for visual polish. Only the live price ticker and the trade history table are actually wired to real trade data from RabbitMQ.