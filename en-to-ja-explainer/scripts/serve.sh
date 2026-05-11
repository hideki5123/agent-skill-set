#!/usr/bin/env bash
# Serve a static site locally and print both localhost and LAN URLs.
# Usage: ./serve.sh <directory> [port]

set -euo pipefail

DIR="${1:-.}"
PORT="${2:-8765}"

if [[ ! -d "$DIR" ]]; then
  echo "Error: directory '$DIR' not found" >&2
  exit 1
fi

# Kill anything already listening on this port (only this user's processes).
if lsof -ti ":$PORT" > /dev/null 2>&1; then
  lsof -ti ":$PORT" | xargs kill 2>/dev/null || true
  sleep 0.3
fi

# Resolve a LAN IP for mobile testing (best-effort, platform-aware).
LAN_IP=""
if command -v ipconfig >/dev/null 2>&1; then
  # macOS
  LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
elif command -v hostname >/dev/null 2>&1; then
  # Linux fallback
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
fi

echo "Serving '$DIR' on:"
echo "  - http://localhost:$PORT/"
if [[ -n "$LAN_IP" ]]; then
  echo "  - http://$LAN_IP:$PORT/   (LAN — phone on the same Wi-Fi)"
fi
echo ""

exec python3 -m http.server "$PORT" --directory "$DIR"
