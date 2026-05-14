"""
Twitch token refresh — called automatically when the access token expires.
Reads TWITCH_REFRESH_TOKEN, TWITCH_CLIENT_ID, and TWITCH_CLIENT_SECRET from
.env, exchanges for a new access token, and writes both new tokens back.
"""
import json
import urllib.parse
import urllib.request
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"


def _read_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _write_env_key(key: str, value: str):
    if not ENV_FILE.exists():
        ENV_FILE.write_text(f"{key}={value}\n")
        return
    lines = ENV_FILE.read_text().splitlines()
    new_lines, replaced = [], False
    for line in lines:
        if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
            new_lines.append(f"{key}={value}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        new_lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(new_lines) + "\n")


def refresh_access_token() -> bool:
    """
    Exchange the stored refresh token for a new access token.
    Writes TWITCH_TOKEN and TWITCH_REFRESH_TOKEN back to .env.
    Returns True on success, False on failure.
    """
    env = _read_env()
    refresh_token  = env.get("TWITCH_REFRESH_TOKEN", "").strip()
    client_id      = env.get("TWITCH_CLIENT_ID", "").strip()
    client_secret  = env.get("TWITCH_CLIENT_SECRET", "").strip()

    if not refresh_token or not client_id or not client_secret:
        print("[Token] Cannot refresh — TWITCH_REFRESH_TOKEN, TWITCH_CLIENT_ID, or "
              "TWITCH_CLIENT_SECRET missing from .env.")
        print("[Token] Run:  python3 get_token.py")
        return False

    payload = urllib.parse.urlencode({
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
        "client_id":     client_id,
        "client_secret": client_secret,
    }).encode()

    try:
        req = urllib.request.Request(
            "https://id.twitch.tv/oauth2/token",
            data=payload,
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[Token] Refresh request failed: {e}")
        return False

    if "access_token" not in data:
        print(f"[Token] Refresh failed — Twitch response: {data}")
        return False

    _write_env_key("TWITCH_TOKEN", f"oauth:{data['access_token']}")
    if "refresh_token" in data:
        _write_env_key("TWITCH_REFRESH_TOKEN", data["refresh_token"])

    print("[Token] Access token refreshed and saved to .env")
    return True
