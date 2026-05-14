"""
StreamPet - Entry point
Runs the FastAPI web server and Twitch bot concurrently.
"""
import asyncio
import uvicorn
from config import cfg
import memory
from server import app


async def run_server():
    config = uvicorn.Config(
        app,
        host=cfg.SERVER_HOST,
        port=cfg.SERVER_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_bot():
    from bot import StreamPetBot
    import twitchio.errors
    import token_manager

    try:
        bot = StreamPetBot()
        await bot.start()
    except twitchio.errors.AuthenticationError:
        print("[Bot] Access token expired — attempting automatic refresh...")
        if token_manager.refresh_access_token():
            print("[Bot] Token refreshed — restarting...")
        else:
            print("[Bot] Auto-refresh failed. Run:  python3 get_token.py")
        raise SystemExit(1)


_PLACEHOLDERS = {"", "your_bot_username", "your_channel_name", "your_token_here"}


def _is_placeholder(value: str) -> bool:
    return not value or value in _PLACEHOLDERS or value.startswith("your_")


async def main():
    memory.init_db()

    if _is_placeholder(cfg.TWITCH_TOKEN) or cfg.TWITCH_TOKEN == "oauth:your_token_here":
        print("[✗] TWITCH_TOKEN is not set in .env.")
        print("    Run:  python3 get_token.py")
        raise SystemExit(1)

    if _is_placeholder(cfg.TWITCH_CHANNEL):
        print("[✗] TWITCH_CHANNEL is still a placeholder in .env.")
        print("    Set it to your Twitch channel name (no # prefix, lowercase).")
        print("    Example:  TWITCH_CHANNEL=mychannel")
        raise SystemExit(1)

    if _is_placeholder(cfg.TWITCH_USERNAME):
        print("[✗] TWITCH_USERNAME is still a placeholder in .env.")
        print("    Set it to your bot account's Twitch username (lowercase).")
        print("    Example:  TWITCH_USERNAME=mybotname")
        raise SystemExit(1)

    print(f"[*] Starting StreamPet")
    print(f"    Pet name  : {cfg.PET_NAME}")
    print(f"    Channel   : #{cfg.TWITCH_CHANNEL}")
    print(f"    LLM model : {cfg.OLLAMA_MODEL}")
    print(f"    Browser   : http://localhost:{cfg.SERVER_PORT}")

    await asyncio.gather(
        run_server(),
        run_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
