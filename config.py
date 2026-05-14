import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Twitch — app credentials (from dev.twitch.tv/console)
    TWITCH_CLIENT_ID: str = os.getenv("TWITCH_CLIENT_ID", "")
    TWITCH_CLIENT_SECRET: str = os.getenv("TWITCH_CLIENT_SECRET", "")
    # User access token written by get_token.py
    TWITCH_TOKEN: str = os.getenv("TWITCH_TOKEN", "")
    TWITCH_USERNAME: str = os.getenv("TWITCH_USERNAME", "StreamPetBot")
    TWITCH_CHANNEL: str = os.getenv("TWITCH_CHANNEL", "")

    # LLM
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Pet personality
    PET_NAME: str = os.getenv("PET_NAME", "Pixel")
    PET_PERSONALITY: str = os.getenv(
        "PET_PERSONALITY",
        "You are a cute, friendly, and witty stream pet. Keep answers to 1-3 sentences. Be fun and engaging."
    )

    # Server
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8765"))

    # TTS (Piper)
    PIPER_BINARY: str = os.getenv("PIPER_BINARY", "./piper/piper")
    PIPER_MODEL: str = os.getenv("PIPER_MODEL", "./piper/en_US-amy-medium.onnx")

    # Cooldown in seconds per user
    COOLDOWN_SECONDS: int = int(os.getenv("COOLDOWN_SECONDS", "15"))

    # Max LLM response tokens
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "150"))

cfg = Config()
