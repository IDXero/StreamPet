import asyncio
import os
import time
import uuid
import glob
from config import cfg

AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


async def synthesize(text: str) -> str | None:
    """Run Piper TTS and return the URL path to the generated WAV file."""
    _cleanup_old_audio()

    filename = f"{uuid.uuid4().hex}.wav"
    out_path = os.path.join(AUDIO_DIR, filename)

    cmd = [
        cfg.PIPER_BINARY,
        "--model", cfg.PIPER_MODEL,
        "--output_file", out_path,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(input=text.encode()), timeout=30)

        if proc.returncode != 0:
            print(f"[TTS] Piper error: {stderr.decode()}")
            return None

        return f"/audio/{filename}"
    except FileNotFoundError:
        print(f"[TTS] Piper binary not found at: {cfg.PIPER_BINARY}")
        print("[TTS] Run install.sh to download Piper.")
        return None
    except asyncio.TimeoutError:
        print("[TTS] Piper timed out.")
        return None


def _cleanup_old_audio(max_age_seconds: int = 300):
    """Delete audio files older than max_age_seconds to keep disk usage low."""
    now = time.time()
    for f in glob.glob(os.path.join(AUDIO_DIR, "*.wav")):
        if now - os.path.getmtime(f) > max_age_seconds:
            try:
                os.remove(f)
            except OSError:
                pass
