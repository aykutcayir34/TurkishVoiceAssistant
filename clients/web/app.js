// Sohbet web istemcisi: mikrofon yakalama + WS + akıcı oynatma + barge-in flush.
"use strict";

const SERVER_SR = 16000; // sunucuya gönderilen ses
const els = {
  mic: document.getElementById("micBtn"),
  send: document.getElementById("sendBtn"),
  text: document.getElementById("textInput"),
  state: document.getElementById("state"),
  log: document.getElementById("log"),
};

let ws = null;
let audioCtx = null;
let micStream = null;
let processor = null;
let sourceNode = null;

// --- Oynatma kuyruğu (barge-in'de anında boşaltılır) ---
let playCtx = null;
let playCursor = 0;
let activeSources = [];

function log(role, text, cls = "") {
  const div = document.createElement("div");
  div.className = `msg ${role} ${cls}`.trim();
  div.textContent = text;
  els.log.appendChild(div);
  els.log.scrollTop = els.log.scrollHeight;
  return div;
}

function setState(s) {
  const map = { listening: "dinliyor", thinking: "düşünüyor", speaking: "konuşuyor", idle: "boşta" };
  els.state.textContent = map[s] || s;
  els.state.className = "state " + s;
}

// ---------------------------------------------------------------------------
// WebSocket
// ---------------------------------------------------------------------------
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => log("system", "Bağlandı.");
  ws.onclose = () => log("system", "Bağlantı kapandı.");
  ws.onmessage = (ev) => handleServer(JSON.parse(ev.data));
}

let currentAssistantEl = null;

function handleServer(msg) {
  switch (msg.type) {
    case "partial_transcript":
      setState("listening");
      break;
    case "final_transcript":
      log("user", msg.text);
      setState("thinking");
      currentAssistantEl = null;
      break;
    case "assistant_token":
      setState("speaking");
      if (!currentAssistantEl) currentAssistantEl = log("assistant", "");
      currentAssistantEl.textContent += msg.text;
      break;
    case "tts_audio":
      playPCM(msg.data, msg.sample_rate);
      break;
    case "interrupted":
      flushPlayback();
      if (currentAssistantEl) currentAssistantEl.classList.add("interrupted");
      currentAssistantEl = null;
      log("system", "— kesildi —");
      break;
    case "turn_end":
      setState("idle");
      currentAssistantEl = null;
      break;
    case "error":
      log("system", "Hata: " + msg.message);
      break;
  }
}

// ---------------------------------------------------------------------------
// Oynatma
// ---------------------------------------------------------------------------
function ensurePlayCtx() {
  if (!playCtx) {
    playCtx = new (window.AudioContext || window.webkitAudioContext)();
    playCursor = playCtx.currentTime;
  }
}

function playPCM(b64, sampleRate) {
  ensurePlayCtx();
  const bytes = atob(b64);
  const buf = new ArrayBuffer(bytes.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < bytes.length; i++) view[i] = bytes.charCodeAt(i);
  const pcm = new Int16Array(buf);
  const audioBuf = playCtx.createBuffer(1, pcm.length, sampleRate);
  const ch = audioBuf.getChannelData(0);
  for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 32768;

  const src = playCtx.createBufferSource();
  src.buffer = audioBuf;
  src.connect(playCtx.destination);
  const startAt = Math.max(playCtx.currentTime, playCursor);
  src.start(startAt);
  playCursor = startAt + audioBuf.duration;
  activeSources.push(src);
  src.onended = () => {
    activeSources = activeSources.filter((s) => s !== src);
  };
}

function flushPlayback() {
  // Barge-in: planlanmış tüm sesi anında durdur (sessizliğe en hızlı yol).
  for (const s of activeSources) {
    try { s.stop(); } catch (e) {}
  }
  activeSources = [];
  if (playCtx) playCursor = playCtx.currentTime;
}

// ---------------------------------------------------------------------------
// Mikrofon yakalama
// ---------------------------------------------------------------------------
function downsample(input, inRate, outRate) {
  if (outRate >= inRate) return input;
  const ratio = inRate / outRate;
  const outLen = Math.floor(input.length / ratio);
  const out = new Int16Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const s = Math.max(-1, Math.min(1, input[Math.floor(i * ratio)]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out;
}

function pcmToB64(int16) {
  const bytes = new Uint8Array(int16.buffer);
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

let silenceTimer = null;
let speaking = false;

async function startMic() {
  micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  sourceNode = audioCtx.createMediaStreamSource(micStream);
  processor = audioCtx.createScriptProcessor(4096, 1, 1);
  sourceNode.connect(processor);
  processor.connect(audioCtx.destination);

  processor.onaudioprocess = (e) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const input = e.inputBuffer.getChannelData(0);
    const down = downsample(input, audioCtx.sampleRate, SERVER_SR);
    ws.send(JSON.stringify({ type: "audio_chunk", data: pcmToB64(down), sample_rate: SERVER_SR }));

    // Basit istemci-taraf sessizlik tespiti -> konuşma sonunda audio_end.
    let energy = 0;
    for (let i = 0; i < input.length; i++) energy += input[i] * input[i];
    energy = Math.sqrt(energy / input.length);
    if (energy > 0.02) {
      speaking = true;
      if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
    } else if (speaking && !silenceTimer) {
      silenceTimer = setTimeout(() => {
        speaking = false;
        silenceTimer = null;
        ws.send(JSON.stringify({ type: "audio_end" }));
      }, 800);
    }
  };
  els.mic.textContent = "🔴 Dinleniyor (kapatmak için tıkla)";
  setState("listening");
}

function stopMic() {
  if (processor) processor.disconnect();
  if (sourceNode) sourceNode.disconnect();
  if (micStream) micStream.getTracks().forEach((t) => t.stop());
  processor = sourceNode = micStream = null;
  els.mic.textContent = "🎤 Mikrofonu Aç";
  setState("idle");
}

let micOn = false;
els.mic.onclick = async () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) connect();
  micOn = !micOn;
  if (micOn) { try { await startMic(); } catch (e) { log("system", "Mikrofon hatası: " + e.message); micOn = false; } }
  else stopMic();
};

els.send.onclick = () => {
  const t = els.text.value.trim();
  if (!t) return;
  if (!ws || ws.readyState !== WebSocket.OPEN) { connect(); setTimeout(() => sendText(t), 300); }
  else sendText(t);
  els.text.value = "";
};
els.text.addEventListener("keydown", (e) => { if (e.key === "Enter") els.send.onclick(); });

function sendText(t) {
  ws.send(JSON.stringify({ type: "text", text: t }));
}

connect();
