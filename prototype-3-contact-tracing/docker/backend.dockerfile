FROM debian:trixie-slim
ARG TARGET=x86_64-unknown-linux-gnu
ARG PROFILE=release

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY target/$TARGET/$PROFILE/backend /backend
COPY frontend/dist /frontend/dist

ENTRYPOINT ["/backend"]
