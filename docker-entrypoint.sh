#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $*"; }
info() { echo -e "${YELLOW}[*]${NC} $*"; }

# ── Ensure runtime directories exist ─────────────────────────────────────────
mkdir -p /app/static/audio /app/data

# ── Wait for Ollama to be ready ───────────────────────────────────────────────
info "Waiting for Ollama to be ready..."
until curl -sf "${OLLAMA_URL:-http://ollama:11434}/api/tags" > /dev/null 2>&1; do
    sleep 2
done
ok "Ollama is ready"

# ── Pull the LLM model if not already present ─────────────────────────────────
MODEL="${OLLAMA_MODEL:-llama3.2}"
if curl -sf "${OLLAMA_URL:-http://ollama:11434}/api/tags" | grep -q "\"${MODEL}\""; then
    ok "${MODEL} already present"
else
    info "Pulling ${MODEL} — this may take a few minutes on first run..."
    curl -sf -X POST "${OLLAMA_URL:-http://ollama:11434}/api/pull" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"${MODEL}\"}" \
        | while IFS= read -r line; do
            status=$(echo "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || true)
            [ -n "$status" ] && echo "  $status"
        done
    ok "${MODEL} ready"
fi

# ── Start StreamPet ───────────────────────────────────────────────────────────
exec python3 main.py
