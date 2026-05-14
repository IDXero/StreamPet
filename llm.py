import httpx
from config import cfg

_SYSTEM_PROMPT = (
    f"Your name is {cfg.PET_NAME}. {cfg.PET_PERSONALITY} "
    "You live on a Twitch stream and love chatting with viewers. "
    "Never use markdown, asterisks, or formatting in your replies — plain text only. "
    "If a question is inappropriate, decline politely and stay in character."
)


async def ask(question: str, username: str) -> str | None:
    """Send a question to Ollama and return the response text."""
    payload = {
        "model": cfg.OLLAMA_MODEL,
        "prompt": f"{username} asks: {question}",
        "system": _SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "num_predict": cfg.MAX_TOKENS,
            "temperature": 0.8,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{cfg.OLLAMA_URL}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except httpx.ConnectError:
        print(f"[LLM] Cannot connect to Ollama at {cfg.OLLAMA_URL}. Is it running?")
        return None
    except httpx.HTTPStatusError as e:
        print(f"[LLM] HTTP error: {e}")
        return None
    except Exception as e:
        print(f"[LLM] Unexpected error ({type(e).__name__}): {e}")
        return None
