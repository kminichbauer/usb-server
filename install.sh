#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v apt >/dev/null 2>&1; then
  echo "Error: this install script supports Debian/Ubuntu systems with apt."
  exit 1
fi

PACKAGES=(python3 python3-tk usbip usbipd)

echo "Installing required packages for usb-server client..."
sudo apt update
sudo apt install -y "${PACKAGES[@]}"

echo
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not available after installation."
  exit 1
fi

cat <<'EOF'
Installation complete.

Next steps:
  cd "$PROJECT_ROOT"
  ./server.py  # or /usr/bin/python3 server.py
  ./client.py  # or /usr/bin/python3 client.py

If you want to run the client/server GUI, make sure the display is available.
EOF
