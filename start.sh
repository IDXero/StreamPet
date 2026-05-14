#!/usr/bin/env bash
# StreamPet manual start script.
# If the systemd service is installed and running, this script reports its
# status instead of starting a second instance.
set -e
cd "$(dirname "$0")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

# ── Guard: don't double-start if the system service is already running ─────────
if systemctl is-active --quiet streampet.service 2>/dev/null; then
  echo -e "${GREEN}[✓]${NC} streampet.service is already running as a system service."
  echo
  echo "  Useful commands:"
  echo "    sudo systemctl status streampet    — full status"
  echo "    sudo journalctl -u streampet -f   — live logs"
  echo "    sudo systemctl restart streampet  — restart"
  echo "    sudo systemctl stop streampet     — stop"
  echo
  echo "  To run manually instead, stop the service first:"
  echo "    sudo systemctl stop streampet"
  exit 0
fi

# ── Normal manual start ────────────────────────────────────────────────────────
if [ ! -f ".venv/bin/activate" ]; then
  echo -e "${RED}[✗]${NC} Virtual environment not found. Run ./install.sh first."
  exit 1
fi

source .venv/bin/activate

if [ ! -f ".env" ]; then
  echo -e "${RED}[✗]${NC} .env file not found. Run ./install.sh first."
  exit 1
fi

# Start Ollama daemon if not already running
if systemctl is-active --quiet ollama.service 2>/dev/null; then
  : # managed by systemd already
elif ! pgrep -x ollama &>/dev/null; then
  echo -e "${YELLOW}[!]${NC} Starting Ollama daemon..."
  ollama serve &>/tmp/ollama.log &
  sleep 2
fi

VMIP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
PORT=$(grep -E "^SERVER_PORT=" .env | cut -d= -f2 || echo 8765)

echo -e "${GREEN}[*]${NC} Starting StreamPet (manual mode)..."
echo -e "    OBS Browser Source: http://${VMIP}:${PORT}"
echo -e "${CYAN}[i]${NC} Tip: run  sudo bash setup_service.sh  to make this permanent."
echo

python3 main.py
