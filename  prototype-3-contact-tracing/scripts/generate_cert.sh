#!/usr/bin/env bash

(
  mkdir assets
  cd assets
  mkcert "localhost"
)