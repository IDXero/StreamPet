#!/usr/bin/env bash
# StreamPet — System Service Installer
# Installs StreamPet as a systemd system service that starts at boot
# automatically, requires no login session, and restarts on failure.
#
# Run once after install.sh:
#   sudo bash setup_service.sh
#
# Management commands after install:
#   sudo systemctl status streampet
#   sudo systemctl stop streampet
#   sudo systemctl start streampet
#   sudo journalctl -u streampet -f

set -e
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*"; exit 1; }
info() { echo -e "${CYAN}[i]${NC} $*"; }

# ── Privilege check ────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
  fail "This script must be run with sudo:  sudo bash setup_service.sh"
fi

# Detect the real user who invoked sudo
REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo $(logname 2>/dev/null || whoami))}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
PROJECT_DIR="$SCRIPT_DIR"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python3"
ENV_FILE="$PROJECT_DIR/.env"
SERVICE_FILE="/etc/systemd/system/streampet.service"

echo
echo "═══════════════════════════════════════════════════════"
echo "         StreamPet — System Service Installer"
echo "═══════════════════════════════════════════════════════"
echo
info "Project dir  : $PROJECT_DIR"
info "Run as user  : $REAL_USER"
info "Python venv  : $VENV_PYTHON"
info "Env file     : $ENV_FILE"
echo

# ── Pre-flight checks ──────────────────────────────────────────────────────────
[ -f "$VENV_PYTHON" ] || fail ".venv not found. Run ./install.sh first."
[ -f "$ENV_FILE" ]    || fail ".env not found. Run ./install.sh and fill in .env first."

if grep -qE "^TWITCH_TOKEN=oauth:your_token_here$" "$ENV_FILE"; then
  fail ".env still has the placeholder TWITCH_TOKEN. Run: python3 get_token.py"
fi
if grep -qE "^TWITCH_CHANNEL=your_channel_name$" "$ENV_FILE"; then
  fail ".env still has the placeholder TWITCH_CHANNEL. Edit .env before installing the service."
fi

ok "Pre-flight checks passed"

# ── Write the systemd unit file ────────────────────────────────────────────────
echo
echo "▶ Writing $SERVICE_FILE ..."

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=StreamPet — Self-Hosted Twitch Stream Pet
Documentation=file://$PROJECT_DIR/StreamPet_Setup_Guide.pdf
# Start after the network is up and Ollama is ready.
# 'Wants' is used (not 'Requires') so StreamPet still starts even if
# ollama.service is not installed (e.g. if Ollama was installed differently).
After=network-online.target ollama.service
Wants=network-online.target ollama.service

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$PROJECT_DIR

# Load all settings from .env (KEY=value, one per line)
EnvironmentFile=$ENV_FILE

ExecStart=$VENV_PYTHON $PROJECT_DIR/main.py

# Restart on any failure; wait 10s between retries so a crash loop
# doesn't hammer Ollama or Twitch.
Restart=always
RestartSec=10
StartLimitIntervalSec=120
StartLimitBurst=5

# Send all output to the system journal (view with: journalctl -u streampet)
StandardOutput=journal
StandardError=journal
SyslogIdentifier=streampet

# Give the process 30s to shut down gracefully before SIGKILL
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

ok "Service file written"

# ── Reload, enable, start ──────────────────────────────────────────────────────
echo
echo "▶ Reloading systemd and enabling service..."
systemctl daemon-reload
systemctl enable streampet.service
ok "streampet.service enabled (will start at every boot)"

# Check if already running and restart, otherwise start fresh
echo
echo "▶ Starting streampet.service..."
if systemctl is-active --quiet streampet.service; then
  systemctl restart streampet.service
  ok "Service restarted"
else
  systemctl start streampet.service
  ok "Service started"
fi

# Brief wait for it to stabilise
sleep 2

# ── Status summary ─────────────────────────────────────────────────────────────
echo
systemctl status streampet.service --no-pager -l | head -20
echo

echo "═══════════════════════════════════════════════════════"
ok "StreamPet is now a persistent system service!"
echo
echo "  Useful commands:"
echo "  ─────────────────────────────────────────────────────"
echo "  View live logs  :  sudo journalctl -u streampet -f"
echo "  Check status    :  sudo systemctl status streampet"
echo "  Stop            :  sudo systemctl stop streampet"
echo "  Start           :  sudo systemctl start streampet"
echo "  Restart         :  sudo systemctl restart streampet"
echo "  Disable autostart: sudo systemctl disable streampet"
echo "  Remove service  :  sudo bash remove_service.sh"
echo
echo "  OBS Browser Source URL:"
VMIP=$(hostname -I | awk '{print $1}')
PORT=$(grep -E "^SERVER_PORT=" "$ENV_FILE" | cut -d= -f2 || echo 8765)
echo "    http://${VMIP}:${PORT}"
echo "═══════════════════════════════════════════════════════"
