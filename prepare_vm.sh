#!/usr/bin/env bash
# StreamPet — VM Pre-Install Preparation Script
# Installs all system-level prerequisites, cleans up any partial state,
# configures the firewall, then reboots.
#
# Run once as root:
#   sudo bash prepare_vm.sh
#
# After the VM comes back up, proceed with:
#   cd ~/streampet && ./install.sh

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*"; exit 1; }
info() { echo -e "${CYAN}[i]${NC} $*"; }
step() { echo; echo -e "${BOLD}▶ $*${NC}"; }

[ "$EUID" -ne 0 ] && fail "Run with sudo:  sudo bash prepare_vm.sh"

REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || whoami)}"
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
PROJECT_DIR="$REAL_HOME/streampet"

echo
echo "══════════════════════════════════════════════════════════"
echo "         StreamPet — VM Pre-Install Preparation"
echo "══════════════════════════════════════════════════════════"
info "Running as       : root (invoked by $REAL_USER)"
info "Project directory: $PROJECT_DIR"
info "Ubuntu version   : $(lsb_release -ds 2>/dev/null || echo unknown)"
info "Kernel           : $(uname -r)"
echo

# ── 1. Update package lists ────────────────────────────────────────────────────
step "Updating package lists..."
DEBIAN_FRONTEND=noninteractive apt-get update -q
ok "Package lists updated"

# ── 2. NVIDIA driver ───────────────────────────────────────────────────────────
step "Installing NVIDIA driver (nvidia-driver-595-open — recommended for RTX 3060)..."

# Check if already installed and working
if nvidia-smi &>/dev/null; then
  ok "NVIDIA driver already installed and working"
  nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
else
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    nvidia-driver-595-open \
    nvidia-utils-595
  ok "NVIDIA driver installed — will activate after reboot"
fi

# ── 3. Python venv + ensurepip ─────────────────────────────────────────────────
step "Installing python3.14-venv (provides ensurepip for virtualenv creation)..."
DEBIAN_FRONTEND=noninteractive apt-get install -y python3.14-venv python3-venv
ok "python3.14-venv installed"

# Verify ensurepip is now available
if python3 -c "import ensurepip" 2>/dev/null; then
  ok "ensurepip confirmed working"
else
  warn "ensurepip still not importable — install.sh will use the user-local pip fallback"
fi

# ── 4. Useful system tools ─────────────────────────────────────────────────────
step "Installing supporting tools (curl, tmux, aplay for audio testing)..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl \
  tmux \
  alsa-utils \
  build-essential
ok "Supporting tools installed"

# ── 5. Clean up broken partial venv ───────────────────────────────────────────
step "Cleaning up partial/broken .venv from previous attempt..."
VENV_DIR="$PROJECT_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
  # Check if the venv has pip (it won't if ensurepip was missing)
  if [ ! -f "$VENV_DIR/bin/pip" ]; then
    rm -rf "$VENV_DIR"
    ok "Removed broken .venv (had no pip)"
  else
    ok ".venv already has pip — left intact"
  fi
else
  ok "No existing .venv to clean up"
fi

# ── 6. Firewall — open port 8765 for OBS ──────────────────────────────────────
step "Configuring firewall to allow StreamPet port 8765..."
if command -v ufw &>/dev/null; then
  UFW_STATUS=$(ufw status | head -1)
  info "UFW status: $UFW_STATUS"
  # Allow port 8765 whether or not UFW is active
  ufw allow 8765/tcp comment "StreamPet OBS Browser Source"
  ok "Port 8765/tcp allowed"
  # Also allow SSH in case it isn't already (prevent lockout)
  ufw allow OpenSSH
  ok "SSH rule confirmed"
else
  warn "ufw not found — skipping firewall configuration"
  info "If you have another firewall, open TCP port 8765 manually"
fi

# ── 7. Persist firewall on reboot ─────────────────────────────────────────────
if command -v ufw &>/dev/null; then
  UFW_ACTIVE=$(ufw status | grep -c "Status: active" || true)
  if [ "$UFW_ACTIVE" -gt 0 ]; then
    ok "UFW is active — rules will persist across reboots"
  else
    info "UFW is installed but not enabled — rules are saved for when it is enabled"
  fi
fi

# ── 8. Verify SSH will survive reboot ─────────────────────────────────────────
step "Ensuring SSH service is enabled at boot..."
systemctl enable ssh 2>/dev/null || systemctl enable sshd 2>/dev/null || warn "Could not enable SSH service — verify manually after reboot"
ok "SSH service enabled"

# ── 9. Summary before reboot ──────────────────────────────────────────────────
echo
echo "══════════════════════════════════════════════════════════"
ok "VM preparation complete! Rebooting in 5 seconds..."
echo
echo "  Installed:"
echo "    ✓ NVIDIA driver 595-open (RTX 3060 — activates after reboot)"
echo "    ✓ python3.14-venv + ensurepip"
echo "    ✓ curl, tmux, alsa-utils, build-essential"
echo "    ✓ Firewall: port 8765 allowed"
echo "    ✓ Broken .venv cleaned up"
echo
echo "  After reboot, verify then run the installer:"
echo "    nvidia-smi                  ← GPU should appear"
echo "    python3 -c 'import ensurepip; print(\"ok\")'  ← should print ok"
echo "    cd ~/streampet && ./install.sh"
echo "══════════════════════════════════════════════════════════"
echo

# Give a moment to read the output
sleep 5
reboot
