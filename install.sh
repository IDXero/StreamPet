#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
fail() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

echo "═══════════════════════════════════════════"
echo "         StreamPet Installer"
echo "═══════════════════════════════════════════"

# ── 0. Ask for bot/app name ────────────────────────────────────────────────────────────────────────────
echo
echo "▶ What would you like to name your StreamPet Twitch app?"
echo "  (This is the name entered when registering your app at dev.twitch.tv/console)"
echo "  Press Enter to use the default: StreamPet"
echo
read -rp "  App name: " BOT_APP_NAME
BOT_APP_NAME="${BOT_APP_NAME:-StreamPet}"
ok "App name set to: ${BOT_APP_NAME}"

# ── 1. pip ────────────────────────────────────────────────────────────────────
echo
echo "▶ Installing pip..."
if ! python3 -m pip --version &>/dev/null; then
  curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 -
fi
ok "pip ready"

# ── 2. Python virtual environment ─────────────────────────────────────────────
echo
echo "▶ Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
ok "venv ready (.venv/)"

# ── 3. Python dependencies ────────────────────────────────────────────────────
echo
echo "▶ Installing Python packages..."
pip install -r requirements.txt -q
ok "Python packages installed"

# ── 4. Piper TTS binary ───────────────────────────────────────────────────────
echo
echo "▶ Downloading Piper TTS..."
PIPER_DIR="./piper"
mkdir -p "$PIPER_DIR"

PIPER_VERSION="2023.11.14-2"
PIPER_ARCHIVE="piper_linux_x86_64.tar.gz"
PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/${PIPER_ARCHIVE}"

if [ ! -f "${PIPER_DIR}/piper" ]; then
  echo "  Downloading Piper binary..."
  curl -L "$PIPER_URL" -o "/tmp/${PIPER_ARCHIVE}"
  tar -xzf "/tmp/${PIPER_ARCHIVE}" -C "$PIPER_DIR" --strip-components=1
  rm "/tmp/${PIPER_ARCHIVE}"
  chmod +x "${PIPER_DIR}/piper"
  ok "Piper binary downloaded"
else
  ok "Piper binary already present"
fi

# ── 5. Piper voice model ──────────────────────────────────────────────────────
echo
echo "▶ Downloading Piper voice model (en_US-amy-medium)..."
VOICE_BASE="en_US-amy-medium"
MODEL_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium"

if [ ! -f "${PIPER_DIR}/${VOICE_BASE}.onnx" ]; then
  echo "  Downloading ${VOICE_BASE}.onnx (~60 MB)..."
  curl -L "${MODEL_URL}/${VOICE_BASE}.onnx"      -o "${PIPER_DIR}/${VOICE_BASE}.onnx"
  curl -L "${MODEL_URL}/${VOICE_BASE}.onnx.json" -o "${PIPER_DIR}/${VOICE_BASE}.onnx.json"
  ok "Voice model downloaded"
else
  ok "Voice model already present"
fi

# ── 6. Ollama ─────────────────────────────────────────────────────────────────
echo
echo "▶ Checking Ollama..."
if ! command -v ollama &>/dev/null; then
  warn "Ollama not found. Installing..."
  curl -fsSL https://ollama.com/install.sh | sh
  ok "Ollama installed"
else
  ok "Ollama already installed"
fi

echo
echo "▶ Pulling LLM model (llama3.2 ~2 GB — skip if already pulled)..."
if ollama list 2>/dev/null | grep -q "llama3.2"; then
  ok "llama3.2 already present"
else
  ollama pull llama3.2
  ok "llama3.2 pulled"
fi

# ── 7. Environment config ─────────────────────────────────────────────────────
echo
if [ ! -f ".env" ]; then
  cp .env.example .env
  warn ".env created from .env.example — EDIT IT before starting!"
  warn "  nano .env"
else
  ok ".env already exists"
fi

# ── 8. Placeholder pet images ─────────────────────────────────────────────────
echo
echo "▶ Creating placeholder pet images..."
python3 make_placeholders.py

# ── 9. Audio output directory ─────────────────────────────────────────────────
mkdir -p static/audio

echo
echo "═══════════════════════════════════════════════════════"
ok "StreamPet installed!"
echo
echo "  Next steps (do these in order):"
echo
echo "  1. Get your Twitch credentials:"
echo "     a) https://dev.twitch.tv/console → Register Your Application"
echo "        Name: ${BOT_APP_NAME} | Redirect URI: http://localhost:17563 | Category: Chat Bot"
echo "     b) Copy Client ID + Secret → paste into .env"
echo "     c) Run:  python3 get_token.py   (saves token automatically)"
echo
echo "  2. Drop your pet images into static/:"
echo "     → static/pet_idle.png  (mouth closed)"
echo "     → static/pet_talk.png  (mouth open)"
echo
echo "  3. Install as a persistent system service (starts at every boot):"
echo "     → sudo bash setup_service.sh"
echo
echo "  4. (Or to run manually without the service):"
echo "     → ./start.sh"
echo
echo "  5. Add Browser Source in OBS:"
VMIP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "<VM-IP>")
echo "     → URL: http://${VMIP}:8765   (use VM LAN IP, not localhost)"
echo "     → Enable: Control audio via OBS"
echo "═══════════════════════════════════════════════════════"
