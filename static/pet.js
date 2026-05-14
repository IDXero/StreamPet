/**
 * StreamPet — browser source logic
 *
 * Image files (drop your own PNG files into static/):
 *   pet_idle.png  — mouth closed / default pose
 *   pet_talk.png  — mouth open
 *
 * WebSocket events received from the server:
 *   { type: "thinking", username, question }
 *   { type: "speak",    username, question, answer, audioUrl }
 *   { type: "error",    username }
 */

const IDLE_SRC = "/static/pet_idle.png";
const TALK_SRC = "/static/pet_talk.png";
const TALK_FRAME_MS = 150; // how fast the mouth flaps (ms per frame)
const BUBBLE_LINGER_MS = 4000; // how long bubble stays after audio ends

const petImg   = document.getElementById("pet-img");
const bubble   = document.getElementById("bubble");
const bubbleUser = document.getElementById("bubble-username");
const bubbleText = document.getElementById("bubble-text");

let talkInterval = null;
let hideTimer    = null;
let currentAudio = null;

// ── WebSocket connection with auto-reconnect ──────────────────────────────────

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);

  ws.addEventListener("open",    () => console.log("[WS] connected"));
  ws.addEventListener("close",   () => { console.log("[WS] disconnected — retrying in 3s"); setTimeout(connect, 3000); });
  ws.addEventListener("error",   (e) => console.warn("[WS] error", e));
  ws.addEventListener("message", (e) => {
    try { handleEvent(JSON.parse(e.data)); }
    catch (err) { console.error("[WS] bad message", err); }
  });

  // Keep-alive ping
  setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send("ping"); }, 20000);
}

// ── Event handler ─────────────────────────────────────────────────────────────

function handleEvent(ev) {
  console.log("[event]", ev);

  if (ev.type === "thinking") {
    showBubble(ev.username, null, true);
    stopTalking();
    return;
  }

  if (ev.type === "error") {
    hideBubble();
    stopTalking();
    return;
  }

  if (ev.type === "speak") {
    showBubble(ev.username, ev.answer, false);

    if (ev.audioUrl) {
      playAudio(ev.audioUrl);
    } else {
      // No audio (TTS unavailable) — animate for a fixed duration
      startTalking();
      const estimatedMs = Math.max(2000, (ev.answer || "").length * 50);
      setTimeout(stopTalking, estimatedMs);
      scheduleHideBubble(estimatedMs + BUBBLE_LINGER_MS);
    }
  }
}

// ── Audio playback ────────────────────────────────────────────────────────────

function playAudio(url) {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

  startTalking();

  const audio = new Audio(url);
  currentAudio = audio;

  audio.addEventListener("ended", () => {
    stopTalking();
    scheduleHideBubble(BUBBLE_LINGER_MS);
    currentAudio = null;
  });

  audio.addEventListener("error", (e) => {
    console.warn("[audio] playback error", e);
    stopTalking();
    scheduleHideBubble(BUBBLE_LINGER_MS);
    currentAudio = null;
  });

  // OBS requires a user gesture for autoplay in some versions.
  // "Control audio via OBS" in browser source settings bypasses this.
  audio.play().catch((err) => {
    console.warn("[audio] autoplay blocked:", err);
    stopTalking();
    scheduleHideBubble(BUBBLE_LINGER_MS);
  });
}

// ── Talk animation ────────────────────────────────────────────────────────────

function startTalking() {
  if (talkInterval) return;
  petImg.classList.add("talking");
  let frame = 0;
  talkInterval = setInterval(() => {
    petImg.src = (frame % 2 === 0) ? TALK_SRC : IDLE_SRC;
    frame++;
  }, TALK_FRAME_MS);
}

function stopTalking() {
  if (talkInterval) {
    clearInterval(talkInterval);
    talkInterval = null;
  }
  petImg.src = IDLE_SRC;
  petImg.classList.remove("talking");
}

// ── Bubble helpers ────────────────────────────────────────────────────────────

function showBubble(username, text, isThinking) {
  clearTimeout(hideTimer);
  hideTimer = null;

  bubbleUser.textContent = username ? `@${username}` : "";
  bubbleText.textContent = text || (isThinking ? "thinking" : "");

  bubble.classList.remove("hidden", "thinking");
  if (isThinking) bubble.classList.add("thinking");
}

function hideBubble() {
  bubble.classList.add("hidden");
  bubble.classList.remove("thinking");
}

function scheduleHideBubble(ms) {
  clearTimeout(hideTimer);
  hideTimer = setTimeout(hideBubble, ms);
}

// ── Init ──────────────────────────────────────────────────────────────────────

connect();
