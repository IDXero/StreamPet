FROM python:3.12-slim

WORKDIR /app

# System tools needed for Piper download and curl health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Download Piper TTS binary and voice model at build time ───────────────────
RUN mkdir -p piper && \
    curl -sL "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz" \
    | tar -xz -C piper --strip-components=1 && \
    chmod +x piper/piper

RUN curl -sLo piper/en_US-amy-medium.onnx \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" && \
    curl -sLo piper/en_US-amy-medium.onnx.json \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

# ── Python dependencies ────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY . .

# Generate placeholder pet images and create runtime directories
RUN python3 make_placeholders.py && \
    mkdir -p static/audio data

EXPOSE 8765

ENTRYPOINT ["bash", "docker-entrypoint.sh"]
