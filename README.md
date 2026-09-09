# Middleware Prototypes — RabbitMQ

Three message-driven prototypes built around **RabbitMQ** as a shared middleware, exploring how independent services can communicate asynchronously across different problem domains and, in one case, entirely different tech stacks.

This project was completed as part of *PBT205 — Project-based Learning Studio: Technology* (Torrens University), a subject focused on building software prototypes using middleware and emerging technologies in a team environment.

> This was a collaborative group project, developed and built together by a team of three.

---

## Project context

The brief asked for three independent prototypes, each modelling a different real-world messaging scenario, all built on top of the same middleware:

1. **Chat application** — multi-room, multi-user real-time messaging
2. **Trading system** — a simple order-matching exchange for a single stock
3. **Contact tracing** — a position-tracking system that detects when users occupy the same location

All three share one architectural principle: application components don't talk to each other directly — they publish and subscribe to topics/queues on RabbitMQ, which decouples them completely. This mirrors how real distributed systems (event-driven backends, microservices, IoT pipelines) are commonly designed.

After building and evaluating all three, the team selected the **contact tracing** prototype to extend further into a more complete, production-style product (see `prototype-3-contact-tracing/`), while prototypes 1 and 2 remain as their originally scoped versions.

---

## Common setup: RabbitMQ

All three prototypes require a running RabbitMQ instance. The simplest way to start one locally is via Docker:

```bash
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

This exposes:
- `5672` — the AMQP port used by the applications to connect
- `15672` — the RabbitMQ management UI (`http://localhost:15672`, default login `guest`/`guest`), useful for inspecting exchanges, queues and message flow while testing

Each prototype's own README (linked below) has the specific run instructions for that application.

---

## Prototypes

| # | Prototype | Stack | Status |
|---|-----------|-------|--------|
| 1 | [Chat Application](./prototype-1-chat) | Python, Flask, RabbitMQ (pika) | Complete |
| 2 | [Trading System](./prototype-2-trading) | Python, RabbitMQ | Complete |
| 3 | [Contact Tracing](./prototype-3-contact-tracing) | Rust, Vite/React/TypeScript, PostgreSQL, RabbitMQ, Docker Compose | Complete — extended final product |

---

## 1. Chat Application

A real-time, multi-room chat application. Users pick a username and a room, and exchange messages with everyone else currently in that room.

**How it works:**
RabbitMQ is configured with a **topic exchange** (`chat_exchange`). Each chat room corresponds to a routing key — when a user joins a room, the app creates a temporary, exclusive queue bound to that routing key, so it only receives messages sent to that specific room. Publishing and subscribing are fully decoupled: the sender doesn't know or care who (or how many people) will receive the message.

**Stack:** Python, Flask (web interface + session handling), [pika](https://pika.readthedocs.io/) (RabbitMQ client), vanilla HTML/JS (polling-based UI updates).

**Features:**
- Multiple simultaneous chat rooms
- Multiple users per room
- Real-time message updates (short-interval polling)
- Switch rooms without logging out
- Simple logout flow

**Development process:** the final web application (`app.py`) was reached iteratively. The `previous-versions/` folder inside this prototype keeps the earlier stages for reference — starting from a bare RabbitMQ connection test, through basic publisher/subscriber scripts, a CLI chat client, an early Tkinter GUI attempt, up to the Flask-based web version that became the final product.

Full details, architecture diagram and run instructions: see [`prototype-1-chat/README.md`](./prototype-1-chat/README.md).

---

## 2. Trading System

*(Section to be completed after reviewing the code — placeholder)*

A simplified single-stock exchange (`XYZ Corp`) where traders submit buy/sell orders with a price, and an exchange service matches compatible orders and publishes completed trades.

Full details: see [`prototype-2-trading/README.md`](./prototype-2-trading/README.md).

---

## 3. Contact Tracing

*(Section to be completed after reviewing the code — placeholder)*

A position-tracking system where users move around a shared grid; the system detects and records when two users occupy the same cell at the same time, and lets a user query who they've been in contact with. This was the prototype selected for extended development into the final product, adding a proper GUI, authentication, and persistence.

Full details: see [`prototype-3-contact-tracing/README.md`](./prototype-3-contact-tracing/README.md).

---

## Repository structure

```
middleware-prototypes-rabbitmq/
├── README.md
├── .gitignore
├── prototype-1-chat/
│   ├── README.md
│   ├── app.py
│   ├── rabbitmq_utils.py
│   ├── requirements.txt
│   ├── templates/
│   └── previous-versions/
├── prototype-2-trading/
│   └── ...
└── prototype-3-contact-tracing/
    └── ...
```
