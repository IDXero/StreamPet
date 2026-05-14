#!/usr/bin/env bash
# StreamPet — Remove System Service
# Stops, disables, and deletes the systemd service unit.
# StreamPet files are left intact; only the service registration is removed.
#
# Usage:  sudo bash remove_service.sh

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

[ "$EUID" -ne 0 ] && fail "Run with sudo:  sudo bash remove_service.sh"

SERVICE_FILE="/etc/systemd/system/streampet.service"

echo
echo "═══════════════════════════════════════════════════════"
echo "         StreamPet — Remove System Service"
echo "═══════════════════════════════════════════════════════"
echo

if systemctl is-active --quiet streampet.service 2>/dev/null; then
  echo "▶ Stopping streampet.service..."
  systemctl stop streampet.service
  ok "Stopped"
fi

if systemctl is-enabled --quiet streampet.service 2>/dev/null; then
  echo "▶ Disabling streampet.service..."
  systemctl disable streampet.service
  ok "Disabled (will not start at boot)"
fi

if [ -f "$SERVICE_FILE" ]; then
  echo "▶ Removing $SERVICE_FILE ..."
  rm "$SERVICE_FILE"
  systemctl daemon-reload
  ok "Service file removed"
else
  warn "Service file not found — may already be removed"
fi

echo
ok "Service removed. StreamPet files are still at ~/streampet."
echo "  To run manually:  cd ~/streampet && ./start.sh"
echo "  To reinstall:     sudo bash setup_service.sh"
echo "═══════════════════════════════════════════════════════"
