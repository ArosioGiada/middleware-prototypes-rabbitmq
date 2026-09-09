#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://localhost:8080"
AUTH_URL="$BASE_URL/api/auth"
POSITION_URL="$BASE_URL/api/position"

CURL=(curl -sS)

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "FAIL: required command not found: $1"
    exit 1
  }
}

require_cmd curl
require_cmd jq

register_user() {
  local name="$1"
  local cookie_file="$2"
  local body_file="$3"

  local status
  status="$("${CURL[@]}" \
    -c "$cookie_file" \
    -o "$body_file" \
    -w "%{http_code}" \
    -X POST "$AUTH_URL" \
    -H 'Content-Type: application/json' \
    -d "$(jq -cn --arg name "$name" '{account_name: $name}')"
  )"

  if [[ "$status" != "200" ]]; then
    echo "FAIL: registration for '$name' returned status $status"
    echo "Response body:"
    cat "$body_file"
    exit 1
  fi

  jq -e '.x | numbers' < "$body_file" >/dev/null || {
    echo "FAIL: registration response for '$name' missing numeric x"
    cat "$body_file"
    exit 1
  }

  jq -e '.y | numbers' < "$body_file" >/dev/null || {
    echo "FAIL: registration response for '$name' missing numeric y"
    cat "$body_file"
    exit 1
  }
}

get_cookie_value() {
  local cookie_file="$1"
  local cookie_name="$2"

  awk -v name="$cookie_name" '
    {
      line = $0
      sub(/^#HttpOnly_/, "", line)
      if (line ~ /^#/) next

      n = split(line, f, /[[:space:]]+/)
      if (n >= 7 && f[6] == name) {
        print f[7]
      }
    }
  ' "$cookie_file" | tail -n1
}

move_user() {
  local cookie_file="$1"
  local x="$2"
  local y="$3"

  local body_file="$TMP_DIR/move_$(basename "$cookie_file").txt"
  local status

  status="$("${CURL[@]}" \
    -b "$cookie_file" \
    -o "$body_file" \
    -w "%{http_code}" \
    -X POST "$POSITION_URL" \
    -H 'Content-Type: application/json' \
    -d "$(jq -cn --argjson x "$x" --argjson y "$y" '{x: $x, y: $y}')"
  )"

  if [[ "$status" != "200" ]]; then
    echo "FAIL: move returned status $status"
    echo "Response body:"
    cat "$body_file"
    exit 1
  fi
}

get_contacts() {
  local account_id="$1"
  local body_file="$2"

  local status
  status="$("${CURL[@]}" \
    -o "$body_file" \
    -w "%{http_code}" \
    "$BASE_URL/api/accounts/${account_id}/contacts"
  )"

  if [[ "$status" != "200" ]]; then
    echo "FAIL: contacts request for account_id=$account_id returned status $status"
    echo "Response body:"
    cat "$body_file"
    exit 1
  fi
}

USER1_COOKIES="$TMP_DIR/user1.cookies"
USER2_COOKIES="$TMP_DIR/user2.cookies"
USER1_BODY="$TMP_DIR/user1.json"
USER2_BODY="$TMP_DIR/user2.json"
CONTACTS_BODY="$TMP_DIR/contacts.json"

echo "== Register user #1 =="
register_user "alice" "$USER1_COOKIES" "$USER1_BODY"

USER1_ACCOUNT_ID="$(get_cookie_value "$USER1_COOKIES" "account_id")"
USER1_SESSION_ID="$(get_cookie_value "$USER1_COOKIES" "session_id")"
USER1_X="$(jq -r '.x' < "$USER1_BODY")"
USER1_Y="$(jq -r '.y' < "$USER1_BODY")"

[[ -n "$USER1_ACCOUNT_ID" ]] || { echo "FAIL: account_id missing for user1"; cat "$USER1_COOKIES"; exit 1; }
[[ -n "$USER1_SESSION_ID" ]] || { echo "FAIL: session_id missing for user1"; cat "$USER1_COOKIES"; exit 1; }

echo "user1: account_id=$USER1_ACCOUNT_ID initial_position=($USER1_X,$USER1_Y)"

echo "== Move user #1 to (8,8) =="
move_user "$USER1_COOKIES" 8 8

echo "== Register user #2 =="
register_user "bob" "$USER2_COOKIES" "$USER2_BODY"

USER2_ACCOUNT_ID="$(get_cookie_value "$USER2_COOKIES" "account_id")"
USER2_SESSION_ID="$(get_cookie_value "$USER2_COOKIES" "session_id")"
USER2_X="$(jq -r '.x' < "$USER2_BODY")"
USER2_Y="$(jq -r '.y' < "$USER2_BODY")"

[[ -n "$USER2_ACCOUNT_ID" ]] || { echo "FAIL: account_id missing for user2"; cat "$USER2_COOKIES"; exit 1; }
[[ -n "$USER2_SESSION_ID" ]] || { echo "FAIL: session_id missing for user2"; cat "$USER2_COOKIES"; exit 1; }

echo "user2: account_id=$USER2_ACCOUNT_ID initial_position=($USER2_X,$USER2_Y)"

echo "== Move user #2 to (8,8) =="
move_user "$USER2_COOKIES" 8 8

echo "== Query contacts for user #1 =="
get_contacts "$USER1_ACCOUNT_ID" "$CONTACTS_BODY"

echo "contacts response:"
cat "$CONTACTS_BODY"
echo

COUNT="$(jq 'length' < "$CONTACTS_BODY")"

if [[ "$COUNT" != "1" ]]; then
  echo "FAIL: expected exactly 1 contact, got $COUNT"
  exit 1
fi

echo "OK: exactly one collided account found"