# TurkishVoiceAssistant — *Sohbet*

Açık kaynak modeller ve vektör veritabanı ile çalışan, **full-duplex (çift yönlü) akıcı** bir Türkçe sesli asistan. En kritik özellik **barge-in**: kullanıcı asistan konuşurken sözünü kesebilir; asistan sesini anında durdurur, üretimini iptal eder, o ana kadar söylediklerini hafızaya yazar ve **yeni bağlamla** yeniden cevap verir.

Ürün gereksinimleri için bkz. [`prd.md`](prd.md).

## Mimari

```
İstemci (WebAudio + WS) ─► Orkestrasyon (FastAPI/asyncio)
                              │
        ┌──────────┬─────────┼─────────┬──────────┐
       VAD        STT       LLM       TTS      (RAG)
     Silero  faster-whisper vLLM   XTTS/Piper   │
                              └─ Embedding (bge-m3) ─► Qdrant
```

- **Durum makinesi:** `IDLE → LISTENING → THINKING → SPEAKING → INTERRUPTED` (`src/sohbet/domain/state.py`)
- **Barge-in kritik yolu (<300ms):** istemciye `interrupted` → playback flush → tur `asyncio.Task` iptali → LLM/TTS `aclose` (abort) → söylenen kısım `[kesildi]` olarak hafızaya → `LISTENING` (`src/sohbet/orchestration/barge_in.py`)
- **Pluggable backend'ler:** her model soyut bir arayüz arkasında; **gerçek + mock** implementasyonlar config ile seçilir (`SOHBET_*_BACKEND`). Mock'lar CPU'da, sıfır ML bağımlılığıyla çalışır.

## Hızlı Başlangıç (CPU, mock backend'ler)

```bash
pip install -e ".[dev]"      # hafif çekirdek + test
python scripts/dev_server.py # http://localhost:8080
```

Tarayıcıda `http://localhost:8080` açın. Mikrofonla veya metin kutusuyla test edin; asistan "konuşurken" (mock TTS bip sesi) araya girin — anında susup yeni girdinizi işler.

## Testler

```bash
make test    # unit + integration + e2e, hepsi GPU'suz ve deterministik
```

- `tests/unit` — durum makinesi, hafıza (kesildi işaretleme), chunking, prompt
- `tests/integration` — tam tur akışı ve **barge-in** (kesme + `[kesildi]` kaydı + <300ms + LLM abort)
- `tests/e2e` — WebSocket üzerinden uçtan uca

## Gerçek Model Yığını (GPU)

`.env.example` → `.env` kopyalayıp backend'leri gerçek modellere çevirin, ardından:

```bash
docker compose --profile gpu up --build   # qdrant + app + vllm
python scripts/ingest.py data/docs         # bilgi tabanını doldur
```

Gerçek backend'ler ve önerilen açık kaynak modeller:

| Katman | Gerçek backend | Model |
|--------|----------------|-------|
| VAD | `silero` | Silero VAD |
| STT | `faster_whisper` | Whisper large-v3 |
| LLM | `vllm` | Qwen2.5 / Llama 3.1 / Trendyol / Cosmos |
| Embedding | `bge_m3` | BAAI/bge-m3 |
| Vektör DB | `qdrant` | Qdrant |
| TTS | `xtts` / `piper` | Coqui XTTS-v2 / Piper |

## Proje Yapısı

```
src/sohbet/
  domain/         saf çekirdek (events, state, memory, types)
  interfaces/     soyut backend sözleşmeleri
  backends/       gerçek + mock implementasyonlar + registry
  orchestration/  session, pipeline, barge_in, audio_router
  rag/            ingest, chunking, loaders, retriever, prompt
  transport/      WebSocket endpoint
clients/web/      tarayıcı istemcisi (mic + playback + barge-in flush)
tests/            unit / integration / e2e
```

## Lisans

Bkz. [`LICENSE`](LICENSE).
