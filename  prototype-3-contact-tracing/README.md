# Prototype 3 — Contact Tracing

A distributed contact-tracing system: users move around a shared grid in real time, and the system detects and records whenever two users occupy the same cell at the same time — allowing a later query of who a given user has been in contact with.

## How it works

The system is split into five independently-running parts, communicating through RabbitMQ rather than direct connections:

- **Client Web App** (React/TypeScript) — renders the grid on a canvas, sends the user's movements, and displays real-time updates
- **Backend Server** (Rust) — handles authentication, serves the frontend, and exposes the REST/SSE API the client talks to
- **Tracker** (Rust) — a separate service that listens to every position update, detects collisions (two accounts on the same cell), and answers "who have I been in contact with?" queries
- **PostgreSQL** — stores accounts and sessions
- **RabbitMQ** — the middleware connecting all of the above via three topic exchanges: one for position broadcasts, and a request/response pair for contact queries

A user "logs in" by picking a username (a lightweight session is created immediately — see *Known limitations* below), lands on a random cell on the grid, and can move with the arrow keys. Their position is published to RabbitMQ on every move; the Tracker consumes that stream, keeps an in-memory record of everyone's last known position, and logs a "collision" whenever two accounts land on the same cell. The frontend receives live position updates from every other connected user via Server-Sent Events (SSE), so the whole grid updates in real time without polling.

Querying contacts (via the sidebar search) sends a request to the Tracker over RabbitMQ and streams back the list of account IDs the queried user has crossed paths with, most recent first.

## Stack

| Layer | Technology |
|---|---|
| Backend & Tracker | Rust, [Axum](https://github.com/tokio-rs/axum) (web framework), [lapin](https://github.com/amqp-rs/lapin) (RabbitMQ client), [sqlx](https://github.com/launchbadge/sqlx) (Postgres) |
| Frontend | Vite, React, TypeScript, HTML Canvas (custom rendering engine) |
| Database | PostgreSQL |
| Middleware | RabbitMQ (topic exchanges) |
| Infrastructure | Docker Compose, Bash scripts |

## Running it locally

Requirements: Linux or WSL, Docker, `npm`/`nvm`/`node`, `mkcert`, Rust/Cargo, `sqlx-cli`.

All scripts must be run from the project root (`prototype-3-contact-tracing/`), not from inside `scripts/`.

```bash
scripts/generate_cert.sh    # generates a local HTTPS certificate
scripts/reset_database.sh   # starts Postgres and applies migrations
scripts/build.sh            # builds the frontend and both Rust services, then starts everything
```

Then open **https://localhost:8080**.

To change the size of the grid, edit the `WIDTH` and `HEIGHT` environment variables in `compose.yaml`.

### Running the integration test

`scripts/tests/test.sh` exercises the full flow end-to-end over HTTP (register two users, move them to the same cell, confirm a contact is recorded) without needing to open a browser. Requires `curl` and `jq`.

## Known limitations

These were conscious scope decisions for a time-boxed university prototype, not oversights:

- **No real authentication.** Entering a username creates a new account and session immediately — there's no password and no way to "log back into" an existing account by name. This is intentional for a fast demo flow, not a security feature.
- **Credentials are hardcoded** in `common/src/database.rs` and `common/src/broker.rs` for local development simplicity, matching the default values in `compose.yaml`. A production version would load these from environment variables or a secrets manager instead.
- **No horizontal scaling or data retention policy** for the Tracker — collision data lives in memory for the lifetime of the process.