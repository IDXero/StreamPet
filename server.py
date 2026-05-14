import asyncio
import json
from typing import Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StreamPet")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WebSocket connection manager ──────────────────────────────────────────────

class _Manager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)
        print(f"[WS] Client connected ({len(self._connections)} total)")

    def disconnect(self, ws: WebSocket):
        self._connections.discard(ws) if hasattr(self._connections, "discard") else None
        try:
            self._connections.remove(ws)
        except ValueError:
            pass
        print(f"[WS] Client disconnected ({len(self._connections)} total)")

    async def broadcast(self, data: dict[str, Any]):
        dead = []
        for ws in self._connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = _Manager()


async def broadcast_event(event: dict[str, Any]):
    await manager.broadcast(event)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Keep alive — ignore any incoming messages from the browser
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── Static files ──────────────────────────────────────────────────────────────

app.mount("/audio", StaticFiles(directory="static/audio"), name="audio")
app.mount("/static", StaticFiles(directory="static"), name="static")
