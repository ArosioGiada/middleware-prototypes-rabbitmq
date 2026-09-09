#!/usr/bin/env bash
set -euo pipefail

TARGET="x86_64-unknown-linux-gnu"
PACKAGE_BACKEND="backend"
PACKAGE_TRACKER="tracker"

PROFILE="release"
PROFILE_FLAG="--release"

export TARGET
export PROFILE

sudo -v

(
  cd frontend
  npm install --verbose
  npm run build
)

docker compose up -d postgres
until docker compose exec postgres pg_isready -U admin; do sleep 1; done

cargo build --target $TARGET --package $PACKAGE_BACKEND $PROFILE_FLAG
cargo build --target $TARGET --package $PACKAGE_TRACKER $PROFILE_FLAG

sudo -E docker compose up --build
