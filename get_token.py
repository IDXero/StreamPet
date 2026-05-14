"""
StreamPet — Twitch OAuth Token Generator
=========================================
Works in two modes, detected automatically:

  GUI mode   — script opens your browser; Twitch redirects back automatically.
  Headless / SSH mode — script prints the auth URL; you open it on any machine
               that has a browser, then paste the redirect URL back here.

twitchapps.com/tmi/ is discontinued. This script replaces it using the
official Twitch Authorization Code flow — no third-party websites involved.

Requirements:
  TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET must be in .env
  (instructions are printed if they are missing)

Usage:
  python3 get_token.py
"""

import http.server
import json
import os
import socket
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────

REDIRECT_PORT = 17563
REDIRECT_URI  = f"http://localhost:{REDIRECT_PORT}"
SCOPES        = "chat:read chat:edit"
ENV_FILE      = Path(__file__).parent / ".env"


# ── Environment detection ──────────────────────────────────────────────────────

def is_ssh_session() -> bool:
    """Return True if we are running inside an SSH session (headless)."""
    return bool(
        os.environ.get("SSH_CLIENT")
        or os.environ.get("SSH_TTY")
        or os.environ.get("SSH_CONNECTION")
    )


def get_local_ip() -> str:
    """Best-effort: return the VM's LAN IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "<VM-IP>"


# ── .env helpers ───────────────────────────────────────────────────────────────

def read_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def write_env_key(key: str, value: str):
    """Update or append key=value in .env."""
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


# ── OAuth helpers ──────────────────────────────────────────────────────────────

def build_auth_url(client_id: str) -> str:
    params = urllib.parse.urlencode({
        "client_id":     client_id,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPES,
        "force_verify":  "true",
    })
    return f"https://id.twitch.tv/oauth2/authorize?{params}"


def exchange_code(client_id: str, client_secret: str, code: str) -> str:
    payload = urllib.parse.urlencode({
        "client_id":     client_id,
        "client_secret": client_secret,
        "code":          code,
        "grant_type":    "authorization_code",
        "redirect_uri":  REDIRECT_URI,
    }).encode()
    req = urllib.request.Request(
        "https://id.twitch.tv/oauth2/token",
        data=payload,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if "access_token" not in data:
        raise RuntimeError(f"Token exchange failed: {data}")
    return data["access_token"]


# ── Local callback server ──────────────────────────────────────────────────────

class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    received_code:  str | None = None
    received_error: str | None = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _CallbackHandler.received_code = params["code"][0]
            body = b"<h2>StreamPet authorised! You can close this tab.</h2>"
        elif "error" in params:
            _CallbackHandler.received_error = params.get("error_description", ["Unknown"])[0]
            body = f"<h2>Error: {_CallbackHandler.received_error}</h2>".encode()
        else:
            body = b"<h2>Waiting...</h2>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


def _run_callback_server_background() -> http.server.HTTPServer:
    """Start the callback server in a daemon thread. Returns the server object."""
    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def wait_for_callback(server: http.server.HTTPServer, timeout: int = 300) -> str:
    """Poll until a code or error arrives, or timeout (seconds)."""
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _CallbackHandler.received_code:
            server.shutdown()
            return _CallbackHandler.received_code
        if _CallbackHandler.received_error:
            server.shutdown()
            raise RuntimeError(f"Twitch error: {_CallbackHandler.received_error}")
        time.sleep(0.25)
    server.shutdown()
    raise TimeoutError("Timed out waiting for Twitch callback.")


# ── Headless / SSH flow ────────────────────────────────────────────────────────

def extract_code_from_url(raw: str) -> str:
    """Parse a pasted redirect URL or query string and return the code."""
    raw = raw.strip()
    # Accept full URL or just the query portion
    if "?" in raw:
        raw = raw.split("?", 1)[1]
    if raw.startswith("code=") or "&code=" in raw:
        params = urllib.parse.parse_qs(raw)
        if "code" in params:
            return params["code"][0]
    raise ValueError("Could not find 'code=' in what you pasted.")


def headless_flow(client_id: str, client_secret: str) -> str:
    """SSH/headless path: print URL, optionally use SSH tunnel, fall back to paste."""
    vm_ip = get_local_ip()
    auth_url = build_auth_url(client_id)

    print()
    print("  ┌─────────────────────────────────────────────────────────┐")
    print("  │  SSH / Headless mode detected                           │")
    print("  └─────────────────────────────────────────────────────────┘")
    print()
    print("  You have two options to complete authentication:")
    print()
    print("  ── OPTION A: SSH Port Forwarding (recommended) ───────────")
    print()
    print("    Open a NEW terminal on your LOCAL machine and run:")
    print()
    print(f"      ssh -L 17563:localhost:17563 <your-ssh-user>@{vm_ip}")
    print()
    print("    Keep that terminal open, then open this URL in your")
    print("    local browser and log in as your BOT account:")
    print()
    print(f"    {auth_url}")
    print()
    print("    Twitch will redirect to http://localhost:17563 — the SSH")
    print("    tunnel forwards it to this VM. The token is captured")
    print("    automatically and written to .env.")
    print()
    print("  ── OPTION B: Paste the redirect URL ─────────────────────")
    print()
    print("    1. Open the URL above in any browser.")
    print("    2. Log in as your BOT account and click Authorise.")
    print("    3. Your browser will try to open http://localhost:17563/?code=...")
    print("       and show a 'connection refused' or blank page — that is fine.")
    print("    4. Copy the full URL from your browser's address bar.")
    print("    5. Paste it below and press Enter.")
    print()

    # Start the callback server anyway — catches Option A automatically
    server = _run_callback_server_background()
    print("  (Waiting for callback via SSH tunnel, or paste URL below)")
    print("  Press Ctrl+C to cancel.")
    print()

    # Give Option A ~10 seconds before prompting for paste
    import time
    deadline = time.time() + 10
    while time.time() < deadline:
        if _CallbackHandler.received_code:
            server.shutdown()
            print("  [✓] Callback received via SSH tunnel!")
            return exchange_code(client_id, client_secret, _CallbackHandler.received_code)
        if _CallbackHandler.received_error:
            server.shutdown()
            raise RuntimeError(f"Twitch error: {_CallbackHandler.received_error}")
        time.sleep(0.25)

    # Option A didn't fire — prompt for paste
    while True:
        try:
            pasted = input("  Paste redirect URL (or press Enter to keep waiting): ").strip()
        except KeyboardInterrupt:
            server.shutdown()
            print("\n[!] Cancelled.")
            sys.exit(1)

        if not pasted:
            # Keep waiting for Option A
            try:
                code = wait_for_callback(server, timeout=300)
                print("  [✓] Callback received!")
                return exchange_code(client_id, client_secret, code)
            except TimeoutError:
                print("[✗] Timed out. Re-run the script and try again.")
                sys.exit(1)

        try:
            code = extract_code_from_url(pasted)
            server.shutdown()
            return exchange_code(client_id, client_secret, code)
        except (ValueError, RuntimeError) as e:
            print(f"  [!] {e} — try again.")


# ── GUI flow ───────────────────────────────────────────────────────────────────

def gui_flow(client_id: str, client_secret: str) -> str:
    """GUI path: open browser automatically, wait for redirect."""
    auth_url = build_auth_url(client_id)
    server   = _run_callback_server_background()

    print()
    print("  Opening your browser to Twitch authorisation page...")
    print("  Make sure you are logged in as your BOT account.")
    print()
    print(f"  If the browser didn't open, paste this URL manually:")
    print(f"  {auth_url}")
    print()

    threading.Timer(0.5, lambda: webbrowser.open(auth_url)).start()

    try:
        code = wait_for_callback(server, timeout=300)
    except TimeoutError:
        print("[✗] Timed out. Re-run and try again.")
        sys.exit(1)
    except KeyboardInterrupt:
        server.shutdown()
        print("\n[!] Cancelled.")
        sys.exit(1)

    return exchange_code(client_id, client_secret, code)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("═══════════════════════════════════════════════════════")
    print("          StreamPet — Twitch Token Generator")
    print("═══════════════════════════════════════════════════════")

    env = read_env()
    client_id     = env.get("TWITCH_CLIENT_ID", "").strip()
    client_secret = env.get("TWITCH_CLIENT_SECRET", "").strip()

    PLACEHOLDERS = {"your_client_id_here", "your_client_secret_here", "", "changeme"}
    id_missing  = not client_id  or client_id  in PLACEHOLDERS or "your_" in client_id
    sec_missing = not client_secret or client_secret in PLACEHOLDERS or "your_" in client_secret

    if id_missing or sec_missing:
        print()
        if id_missing and sec_missing:
            print("  TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET still contain placeholder values in .env")
        elif id_missing:
            print("  TWITCH_CLIENT_ID still contains a placeholder value in .env")
        else:
            print("  TWITCH_CLIENT_SECRET still contains a placeholder value in .env")
        print()
        print("  Steps to get them:")
        print("  1. Go to https://dev.twitch.tv/console (log in as your BOT account)")
        print("  2. Click  Register Your Application")
        print("  3. Fill in:")
        print("       Name              : StreamPet  (or any name you like)")
        print(f"      OAuth Redirect URL : {REDIRECT_URI}")
        print("       Category          : Chat Bot")
        print("  4. Click Create → Manage")
        print("  5. Copy Client ID  → add to .env:  TWITCH_CLIENT_ID=...")
        print("  6. Click New Secret → add to .env:  TWITCH_CLIENT_SECRET=...")
        print("  7. Re-run:  python3 get_token.py")
        print()
        sys.exit(1)

    headless = is_ssh_session()

    try:
        if headless:
            token = headless_flow(client_id, client_secret)
        else:
            token = gui_flow(client_id, client_secret)
    except RuntimeError as e:
        print(f"\n[✗] {e}")
        sys.exit(1)

    oauth_token = f"oauth:{token}"
    write_env_key("TWITCH_TOKEN", oauth_token)

    print()
    print("  [✓] Token saved to .env")
    print(f"      {oauth_token[:24]}{'*' * max(0, len(oauth_token) - 24)}")
    print()
    print("  Done. Run:  ./start.sh")
    print("═══════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
