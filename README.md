# StreamPet — Docker Edition

A fully self-hosted Twitch stream overlay pet. Viewers type `!ask <question>` in chat and the pet responds with a spoken, animated reply — generated entirely on your local machine. No cloud APIs required.

> **Branch:** `docker` — containerised deployment via Docker Compose.
> For the bare-metal install, see the [`main` branch](../../tree/main).

![StreamPet demo](static/pet_placeholder.svg)

---

## Features

- **`!ask` command** — viewers ask questions, the pet answers live in chat and on stream
- **Local LLM** — powered by [Ollama](https://ollama.com) (llama3.2 by default, auto-pulled on first run)
- **Local TTS** — [Piper TTS](https://github.com/rhasspy/piper) bundled in the image
- **OBS Browser Source** — transparent overlay with animated mouth-open/closed PNG swap
- **Viewer memory** — remembers past interactions per viewer, tracks regulars
- **Auto token refresh** — Twitch access token renews automatically, no manual re-auth
- **GPU accelerated** — Ollama uses your NVIDIA GPU via the NVIDIA Container Toolkit

---

## Requirements

| | Linux | Windows |
|---|---|---|
| OS | Ubuntu/Debian recommended | Windows 10 21H2+ or Windows 11 |
| Docker | [Docker Engine + Compose](https://docs.docker.com/engine/install/) | [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL2 backend) |
| GPU support | [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) required | Driver 471.11+ on host — WSL2 handles passthrough automatically |
| GPU | NVIDIA Turing or newer (GTX 16xx / RTX 20xx+), minimum 4 GB VRAM | Same |
| Twitch account | Bot account (can be your main) | Same |

GPU is strongly recommended but not required — Ollama runs on CPU if no compatible GPU is found.

---

## Quick Start

### 1. Install NVIDIA Container Toolkit (first time only)

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 2. Clone the docker branch

```bash
git clone -b docker https://github.com/IDXero/StreamPet.git
cd StreamPet
```

### 3. Configure

```bash
cp .env.example .env
nano .env
```

Fill in `TWITCH_USERNAME` and `TWITCH_CHANNEL`. Leave `TWITCH_TOKEN` for the next step.

### 4. Get your Twitch credentials

1. Go to [https://dev.twitch.tv/console](https://dev.twitch.tv/console) — log in as your **bot** account
2. Click **Register Your Application**
   - Name: `StreamPet` (or anything you like)
   - OAuth Redirect URL: `http://localhost:17563`
   - Category: `Chat Bot`
3. Copy the **Client ID** and **Client Secret** into `.env`
4. Run the token helper (SSH/headless mode is auto-detected):

```bash
python3 get_token.py
```

### 5. Build and start

```bash
docker compose up -d --build
```

On first run this will:
- Build the StreamPet image (~5 min, downloads Piper TTS and voice model)
- Pull the `ollama/ollama` image
- Start Ollama and pull `llama3.2` (~2 GB — once only)
- Start StreamPet

Follow logs:
```bash
docker compose logs -f
```

### 6. Add your pet images

Drop your PNG artwork into the running container:

```bash
docker cp pet_idle.png StreamPet-streampet-1:/app/static/pet_idle.png
docker cp pet_talk.png StreamPet-streampet-1:/app/static/pet_talk.png
docker compose restart streampet
```

Placeholder pink rectangles are used until you replace them.

### 7. Add OBS Browser Source

- URL: `http://<your-host-ip>:8765`
- Enable: **Control audio via OBS**

---

## GPU Selection Guide

| Model | VRAM | Suggested GPUs |
|-------|------|----------------|
| llama3.2 3B (default) | ~3 GB | GTX 1660 Super, RTX 2060, RTX 3050, RTX 4060 |
| mistral 7B | ~5 GB | RTX 2060 Super, RTX 2070, RTX 3060, RTX 4060 Ti |
| llama3.1 8B | ~6 GB | RTX 2070 Super, RTX 2080, RTX 3060, RTX 4070 |

Change the model in `.env`: `OLLAMA_MODEL=llama3.1` — the entrypoint pulls it automatically on next start.

---

## Management

```bash
docker compose up -d          # start
docker compose down           # stop
docker compose restart streampet  # restart after .env changes
docker compose logs -f        # live logs
docker compose pull           # update ollama image
docker compose up -d --build  # rebuild after code changes
```

---

## Configuration

All settings live in `.env`. Key options:

| Variable | Description | Default |
|----------|-------------|---------|
| `TWITCH_USERNAME` | Bot account username | — |
| `TWITCH_CHANNEL` | Your channel name (no `#`) | — |
| `PET_NAME` | Pet's name used in LLM prompt | `Pixel` |
| `PET_PERSONALITY` | System prompt personality | friendly, concise |
| `OLLAMA_MODEL` | Model to use (auto-pulled) | `llama3.2` |
| `COOLDOWN_SECONDS` | Per-user cooldown for `!ask` | `15` |
| `MAX_TOKENS` | Max LLM response length | `150` |
| `SERVER_PORT` | HTTP/WebSocket port for OBS | `8765` |

---

## Windows (Docker Desktop)

StreamPet works on Windows via Docker Desktop with a few differences from the Linux setup.

**Prerequisites:**
- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) with the WSL2 backend enabled
- Windows 11 or Windows 10 21H2+ for GPU support
- NVIDIA driver 471.11 or newer installed on the **host** (not inside Docker)

**GPU support:**
Docker Desktop on Windows routes GPU access through WSL2. If your driver and Windows version support it, the Ollama container will use your GPU automatically — no extra configuration needed. If not, Ollama falls back to CPU (slower but functional — expect 30–60s responses instead of 2–5s).

To verify GPU is being used after startup:
```powershell
docker exec StreamPet-ollama-1 ollama ps
```
The output should show your GPU name in the `PROCESSOR` column. If it shows `CPU`, check your driver version.

**Getting your Twitch token on Windows:**
Run `get_token.py` directly on your Windows machine (requires Python installed):
```powershell
python get_token.py
```
It will open your browser automatically — no SSH tunnel needed.

**OBS Browser Source URL:**
Since OBS and Docker are on the same machine, use `localhost`:
```
http://localhost:8765
```

**Replacing pet images on Windows:**
```powershell
docker cp pet_idle.png StreamPet-streampet-1:/app/static/pet_idle.png
docker cp pet_talk.png StreamPet-streampet-1:/app/static/pet_talk.png
docker compose restart streampet
```

---

## Data Persistence

| Data | Storage |
|------|---------|
| LLM models | `ollama_models` Docker volume |
| Viewer memory (`memory.db`) | `streampet_data` Docker volume |
| Runtime audio files | `streampet_audio` Docker volume |

To back up viewer memory:
```bash
docker run --rm -v streampet_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/streampet_data_backup.tar.gz -C /data .
```
