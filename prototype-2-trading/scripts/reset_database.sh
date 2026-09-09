#!/usr/bin/env bash
docker compose up -d postgres
until docker compose exec postgres pg_isready -U admin; do sleep 1; done
cargo sqlx database reset -y
docker compose down







