# Middleware Prototypes — RabbitMQ

Three message-driven prototypes built around **RabbitMQ** as a shared middleware, exploring how independent services can communicate asynchronously across different problem domains and, in one case, entirely different tech stacks.

This project was completed as part of *PBT205 — Project-based Learning Studio: Technology* (Torrens University), a subject focused on building software prototypes using middleware and emerging technologies.

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

<img width="739" height="207" alt="s - chat" src="https://github.com/user-attachments/assets/c241ffee-f90d-4a37-973a-dc9aad256be4" />

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

A simplified single-stock exchange (`XYZ Corp`): traders submit buy/sell orders through a fire-and-forget CLI, and a long-running exchange service matches compatible orders using price-time priority before publishing completed trades — which any number of independent consumers (a terminal listener, a GUI dashboard) can observe simultaneously.

<img width="703" height="334" alt="s - trading" src="https://github.com/user-attachments/assets/fca82a48-2a07-4587-a53b-72ced0e962a4" />

**How it works:** two RabbitMQ queues, `orders` and `trades`, decouple every component. The exchange maintains an in-memory order book and matches a new order the moment a compatible opposite-side order exists at an acceptable price.

**Stack:** Python, pika, Tkinter (GUI).

Full details, run instructions and known limitations: see [`prototype-2-trading/README.md`](./prototype-2-trading/README.md).

---

## 3. Contact Tracing

A distributed contact-tracing system: users move around a shared grid in real time, and the system detects and records whenever two users occupy the same cell at the same time, letting a user later query who they've been in contact with.

<img width="703" height="327" alt="s - tracing" src="https://github.com/user-attachments/assets/0877bd8f-a999-44a5-b240-3c3d22027e6d" />

**How it works:** the system is split into five parts — a React/TypeScript client, a Rust backend, a separate Rust "Tracker" service, PostgreSQL, and RabbitMQ — communicating entirely through message exchanges rather than direct calls. Position updates are published to RabbitMQ on every move and broadcast to all connected clients in real time via Server-Sent Events; the Tracker consumes that same stream independently to detect and log collisions, and answers contact queries asynchronously over a dedicated request/response exchange.

This was the prototype selected for extended development into the final product: a proper canvas-based GUI with pan/zoom, a lightweight session system, PostgreSQL persistence, and an end-to-end integration test.

**Stack:** Rust (Axum, lapin, sqlx), React/TypeScript (Vite, HTML Canvas), PostgreSQL, RabbitMQ, Docker Compose.

Full details, architecture, run instructions and known limitations: see [`prototype-3-contact-tracing/README.md`](./prototype-3-contact-tracing/README.md).

---

> This was a collaborative group project, developed and built together by a team of three.
This repository is a curated, cleaned-up version of the original coursework project, prepared for portfolio purposes. Minor issues — hardcoded values, leftover debug logging, missing dependency files, and outdated documentation — have been reviewed and fixed after the original submission.
