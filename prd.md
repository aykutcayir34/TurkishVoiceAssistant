# Ürün Gereksinim Dokümanı (PRD) — Türkçe Sesli Asistan

| Alan | Değer |
|------|-------|
| Ürün Adı | TurkishVoiceAssistant (kod adı: *Sohbet*) |
| Doküman Sürümü | 1.0 |
| Tarih | 2026-07-01 |
| Durum | Taslak |
| Sahip | Ürün / AI Ekibi |

---

## 1. Amaç ve Özet

Bu doküman, **tamamen açık kaynak kodlu modeller** ve bir **vektör veritabanı** üzerine kurulu, Türkçe konuşan bir **sesli asistanın** ürün ve teknik gereksinimlerini tanımlar.

Asistanın en kritik özelliği **akıcı ve doğal bir konuşma deneyimi** sunmasıdır:

- Kullanıcı, asistan konuşurken **sözünü kesebilir** (barge-in / kesme).
- Asistan konuşmayı **anında durdurur**, kullanıcının yeni girdisini dinler.
- Asistan, **yeni bağlamı** dikkate alarak (önceki cevabı ve kesintiyi hafızada tutarak) yeniden cevap üretir.

Amaç; bulut tabanlı ticari servislere (OpenAI, Google, Azure) bağımlı olmadan, veri gizliliğini koruyan, yerelde veya kendi sunucumuzda çalışabilen, düşük gecikmeli (low-latency) bir Türkçe sesli diyalog sistemi kurmaktır.

---

## 2. Hedefler ve Başarı Kriterleri

### 2.1 Ürün Hedefleri
1. Doğal, kesintiye izin veren, tam çift yönlü (full-duplex) Türkçe konuşma.
2. RAG (Retrieval-Augmented Generation) ile bilgi tabanına dayalı, halüsinasyonu düşük cevaplar.
3. Uçtan uca açık kaynak yığın — ticari API bağımlılığı yok.
4. Konuşma bağlamının (hafıza) oturum boyunca korunması.

### 2.2 Ölçülebilir Başarı Kriterleri (KPI)

| Metrik | Hedef |
|--------|-------|
| Kesmeden ilk sese kadar gecikme (barge-in tepki) | < 300 ms |
| Konuşma bitişinden ilk cevaba kadar gecikme (turn latency, P50) | < 1.2 sn |
| STT Kelime Hata Oranı (WER) — Türkçe | < %12 |
| Kesme (barge-in) doğru algılama oranı | > %95 |
| RAG cevap doğruluğu (insan değerlendirmesi) | > %85 |
| TTS doğallık (MOS) | > 4.0 / 5 |

---

## 3. Kapsam

### 3.1 Kapsam İçi (v1)
- Türkçe sesli giriş → metin (STT)
- Niyet + RAG destekli cevap üretimi (LLM + vektör DB)
- Metin → Türkçe sesli çıkış (TTS)
- Barge-in (kullanıcının modeli konuşarak kesmesi) ve bağlam güncelleme
- Konuşma geçmişi / kısa süreli hafıza
- Doküman yükleme ve vektör veritabanına gömme (ingest)

### 3.2 Kapsam Dışı (v1)
- Çok dilli destek (yalnızca Türkçe; mimari genişletilebilir)
- Sesli kimlik doğrulama / konuşmacı tanıma (v2 aday)
- Mobil uygulama (v1 web + WebSocket istemcisi)
- Duygu analizi / ses tonu adaptasyonu (v2 aday)

---

## 4. Kullanıcı Personaları ve Senaryolar

### 4.1 Personalar
- **Son kullanıcı:** Türkçe konuşarak bilgi almak isteyen kişi (müşteri hizmetleri, kişisel asistan, kurum içi bilgi bankası).
- **İçerik yöneticisi:** Bilgi tabanına doküman ekleyen/güncelleyen kişi.

### 4.2 Ana Kullanıcı Senaryosu — Kesme (Barge-in)

> **Kullanıcı:** "Ankara'nın hava durumu nasıl, yarın için..."
> **Asistan:** "Ankara için yarın parçalı bulutlu, en yüksek 28 derece bekleni-"
> **Kullanıcı (asistanı keserek):** "Yok, İstanbul'u kastetmiştim."
> **Asistan (anında susar, yeni bağlamla):** "İstanbul için yarın güneşli, en yüksek 31 derece bekleniyor."

Bu senaryoda sistem:
1. Kullanıcının sesini asistan konuşurken algılar (VAD).
2. TTS oynatmasını < 300 ms içinde durdurur.
3. Yarım kalan cevabı ("...bekleni-") ve yeni girdiyi bağlama ekler.
4. Yeni niyeti (İstanbul) çözer ve cevabı yeniden üretir.

---

## 5. Fonksiyonel Gereksinimler

### 5.1 Ses Yakalama ve VAD
- **FR-1:** Sistem mikrofon akışını sürekli (streaming) olarak yakalamalıdır.
- **FR-2:** Ses Etkinliği Tespiti (VAD) ile konuşma başı/sonu tespit edilmelidir.
- **FR-3:** VAD, asistan konuşurken de aktif çalışarak barge-in tetiklemelidir (echo cancellation ile kendi sesini filtrelemeli).

### 5.2 Konuşma Tanıma (STT)
- **FR-4:** Türkçe konuşma gerçek zamanlı (streaming) metne çevrilmelidir.
- **FR-5:** Kısmi (partial) transkripsiyonlar döndürülebilmelidir (düşük gecikme için).

### 5.3 Diyalog Yönetimi ve RAG
- **FR-6:** Kullanıcı sorusu, vektör veritabanında anlamsal arama (semantic search) ile ilgili dokümanları getirmelidir.
- **FR-7:** LLM, getirilen bağlam + konuşma geçmişi ile cevap üretmelidir (streaming token çıkışı).
- **FR-8:** Konuşma geçmişi (hafıza) oturum boyunca korunmalı ve her turda LLM'e verilmelidir.

### 5.4 Barge-in ve Bağlam Güncelleme (Kritik)
- **FR-9:** Kullanıcı konuşmaya başladığında asistan TTS çıkışı derhal durdurulmalıdır.
- **FR-10:** Durdurulan cevabın **yalnızca sesli olarak söylenmiş kısmı** (spoken-so-far) hafızaya yazılmalıdır; söylenmeyen kısım atılmalıdır.
- **FR-11:** LLM üretimi (generation) iptal edilebilir (cancellable) olmalıdır; kesme anında token üretimi durdurulur.
- **FR-12:** Yeni kullanıcı girdisi, güncellenmiş bağlamla yeni bir tur olarak işlenmelidir.

### 5.5 Sesli Çıkış (TTS)
- **FR-13:** LLM token'ları geldikçe cümle bazında (streaming) sese çevrilmelidir (ilk sese kadar gecikmeyi azaltmak için).
- **FR-14:** TTS oynatması anında durdurulabilir (interruptible playback) olmalıdır.

### 5.6 Bilgi Tabanı Yönetimi
- **FR-15:** Doküman yükleme (PDF, TXT, Markdown, HTML) desteklenmelidir.
- **FR-16:** Dokümanlar parçalara (chunk) ayrılıp gömülerek (embedding) vektör veritabanına yazılmalıdır.
- **FR-17:** Kaynak referansları (citation) cevapla birlikte tutulmalıdır.

---

## 6. Fonksiyonel Olmayan Gereksinimler

| Kod | Gereksinim |
|-----|-----------|
| NFR-1 | **Gecikme:** Uçtan uca tur gecikmesi P50 < 1.2 sn, barge-in tepkisi < 300 ms. |
| NFR-2 | **Gizlilik:** Tüm işleme yerel/kendi sunucuda; ses verisi dışarı gönderilmez. |
| NFR-3 | **Ölçeklenebilirlik:** Modeller servis olarak (microservice) ayrıştırılabilir, GPU üzerinde batch destekli. |
| NFR-4 | **Açık kaynak:** Tüm modeller izin verici (permissive) veya araştırma dostu lisanslı olmalı. |
| NFR-5 | **Gözlemlenebilirlik:** Her turda gecikme, WER, RAG isabet metrikleri loglanmalı. |
| NFR-6 | **Dayanıklılık:** Ağ/servis kesintilerinde asistan zarif (graceful) hata mesajı vermeli. |

---

## 7. Teknik Mimari

### 7.1 Yüksek Seviye Akış

```
                     ┌─────────────────────────────────────────────┐
                     │              İstemci (Web / WS)              │
                     │   Mikrofon akışı ─┐        ▲ Hoparlör (TTS)  │
                     └───────────────────┼────────┼────────────────┘
                                         │ ses    │ ses
                                         ▼        │
                     ┌───────────────────────────┴────────────────┐
                     │            Orkestrasyon Servisi             │
                     │  (WebSocket, tur yönetimi, barge-in mantığı)│
                     └───┬─────────┬──────────┬──────────┬─────────┘
                         │         │          │          │
                  ┌──────▼──┐ ┌────▼───┐ ┌────▼────┐ ┌───▼─────┐
                  │  VAD    │ │  STT   │ │   LLM   │ │  TTS    │
                  │(Silero) │ │(Whisper│ │(Türkçe  │ │(XTTS /  │
                  │         │ │ faster)│ │  LLM)   │ │ Piper)  │
                  └─────────┘ └────────┘ └────┬────┘ └─────────┘
                                              │ retrieve
                                        ┌─────▼──────┐
                                        │  Vektör DB │
                                        │  (Qdrant)  │
                                        └────────────┘
```

### 7.2 Konuşma Turu Durum Makinesi (State Machine)

```
IDLE ──(kullanıcı konuşur)──► LISTENING ──(sessizlik/VAD end)──► THINKING
  ▲                                                                  │
  │                                                          (LLM streaming)
  │                                                                  ▼
  └──(cevap biter)── SPEAKING ◄──(TTS streaming başlar)───────── SPEAKING
                        │
                        │ (kullanıcı konuşmaya başlar = BARGE-IN)
                        ▼
                    INTERRUPTED ──► (TTS durdur, LLM iptal et,
                                      söylenen kısmı hafızaya yaz)
                                         │
                                         ▼
                                     LISTENING (yeni bağlam)
```

**Barge-in kritik yol:** `SPEAKING` durumundayken VAD konuşma tespit ederse:
1. TTS playback buffer temizlenir (flush) → ses susar.
2. LLM generation isteği iptal edilir (cancel token / abort).
3. `spoken_so_far` metni "assistant" mesajı olarak hafızaya eklenir (kesildi işaretiyle).
4. Durum `LISTENING`'e geçer; yeni STT sonucu yeni tur başlatır.

---

## 8. Açık Kaynak Model Seçimleri

> Tüm bileşenler açık kaynak; aşağıda birincil öneri ve alternatifler verilmiştir. Nihai seçim, benchmark ve donanım kısıtlarına göre yapılacaktır (bkz. Bölüm 12).

### 8.1 VAD (Ses Etkinliği Tespiti)
| Öneri | Alternatif |
|-------|-----------|
| **Silero VAD** (hafif, düşük gecikme, MIT) | WebRTC VAD, `pyannote` |

### 8.2 STT (Konuşma Tanıma) — Türkçe
| Öneri | Alternatif |
|-------|-----------|
| **faster-whisper** (Whisper large-v3 / turbo, CTranslate2 ile hızlandırılmış) | `whisper.cpp`, NVIDIA NeMo, Wav2Vec2-TR |
| Not: Streaming için `whisper-streaming` veya VAD tabanlı chunk'lama | — |

### 8.3 LLM — Türkçe Üretken Model
| Öneri | Alternatif |
|-------|-----------|
| **Qwen2.5 / Llama 3.1 (instruct, Türkçe güçlü)** | Trendyol-LLM, Cosmos (ytu-ce-cosmos/Turkish-Llama), Gemma 2, Mistral |
| Servis: **vLLM** (yüksek verim, streaming, iptal desteği) | Ollama, TGI (Text Generation Inference) |

### 8.4 Embedding (Gömme) — Türkçe / Çok Dilli
| Öneri | Alternatif |
|-------|-----------|
| **BAAI/bge-m3** (çok dilli, güçlü Türkçe) | `intfloat/multilingual-e5-large`, `jinaai/jina-embeddings-v3` |

### 8.5 Vektör Veritabanı
| Öneri | Alternatif |
|-------|-----------|
| **Qdrant** (açık kaynak, hızlı, hibrit arama, filtreleme, Docker) | Milvus, Weaviate, Chroma, pgvector |

### 8.6 TTS (Metin → Ses) — Türkçe
| Öneri | Alternatif |
|-------|-----------|
| **Coqui XTTS-v2** (çok dilli, ses klonlama, doğal Türkçe) | Piper (hafif, düşük gecikme), Fish-Speech, MMS-TTS-tur |

---

## 9. RAG (Retrieval-Augmented Generation) Boru Hattı

### 9.1 İndeksleme (Offline / Ingest)
1. Doküman yükle → temizle (parse).
2. Parçala (chunking): ~500-800 token, %10-15 örtüşme (overlap).
3. Embedding üret (bge-m3).
4. Qdrant'a yaz (metin + metadata + kaynak).

### 9.2 Sorgulama (Online / Runtime)
1. Kullanıcı sorusunu embed et.
2. Qdrant'ta top-k (k=5) anlamsal arama + opsiyonel hibrit (BM25 + vektör).
3. Yeniden sıralama (reranking, ör. `bge-reranker`) — opsiyonel.
4. Getirilen bağlamı + konuşma geçmişini prompt'a yerleştir.
5. LLM'e gönder → streaming cevap.
6. Kaynak referanslarını (citation) cevaba iliştir.

### 9.3 Prompt Şablonu (Türkçe)
```
Sen yardımcı bir Türkçe sesli asistansın. Kısa, akıcı ve doğal konuş.
Aşağıdaki bağlamı kullanarak soruyu yanıtla. Bağlamda cevap yoksa
bilmediğini dürüstçe söyle.

[BAĞLAM]
{retrieved_chunks}

[KONUŞMA GEÇMİŞİ]
{conversation_history}

[KULLANICI]
{user_query}
```

---

## 10. Hafıza (Bağlam) Yönetimi

- **Kısa süreli hafıza:** Aktif oturumdaki tüm turlar (kullanıcı + asistan mesajları). Token limiti aşılırsa özetleme (summarization) uygulanır.
- **Kesme (barge-in) kaydı:** Kesilen asistan cevabı `"[kesildi] {spoken_so_far}"` biçiminde tutulur ki model neyin yarım kaldığını bilsin.
- **Uzun süreli hafıza (v2 aday):** Kullanıcı tercihleri vektör DB'de ayrı koleksiyonda saklanabilir.

**Örnek hafıza durumu (barge-in sonrası):**
```json
[
  {"role": "user", "content": "Ankara'nın hava durumu nasıl, yarın için..."},
  {"role": "assistant", "content": "[kesildi] Ankara için yarın parçalı bulutlu, en yüksek 28 derece bekleni-"},
  {"role": "user", "content": "Yok, İstanbul'u kastetmiştim."}
]
```

---

## 11. API / Arayüz Tasarımı (Taslak)

İstemci ↔ Orkestrasyon iletişimi **WebSocket** üzerinden çift yönlü akışla yapılır.

**İstemci → Sunucu mesajları:**
```json
{"type": "audio_chunk", "data": "<base64 pcm>"}
{"type": "audio_end"}
```

**Sunucu → İstemci mesajları:**
```json
{"type": "partial_transcript", "text": "ankara'nın hava"}
{"type": "final_transcript",   "text": "ankara'nın hava durumu nasıl"}
{"type": "assistant_token",    "text": "Ankara için "}
{"type": "tts_audio",          "data": "<base64 pcm>"}
{"type": "interrupted"}   // barge-in tetiklendiğinde
{"type": "turn_end"}
```

---

## 12. Teknoloji Yığını (Özet)

| Katman | Teknoloji |
|--------|-----------|
| İstemci | Web (JS/TS), WebAudio API, WebSocket |
| Orkestrasyon | Python (FastAPI / asyncio) veya Go |
| VAD | Silero VAD |
| STT | faster-whisper (large-v3-turbo) |
| LLM Servisi | vLLM + Türkçe uyumlu açık model |
| Embedding | bge-m3 |
| Vektör DB | Qdrant |
| TTS | Coqui XTTS-v2 / Piper |
| Dağıtım | Docker Compose / Kubernetes, GPU (CUDA) |

---

## 13. Aşamalar / Yol Haritası

### Faz 1 — Temel Boru Hattı (MVP)
- STT → LLM → TTS uçtan uca akış (kesme yok).
- Qdrant ile temel RAG.
- Web istemci + WebSocket.

### Faz 2 — Akıcılık ve Barge-in
- VAD tabanlı barge-in.
- İptal edilebilir LLM generation + TTS flush.
- `spoken_so_far` hafıza güncellemesi.
- Streaming TTS (cümle bazlı).

### Faz 3 — Kalite ve Ölçeklendirme
- Reranking, hibrit arama.
- Hafıza özetleme.
- Gözlemlenebilirlik / metrik paneli.
- Yük testi ve gecikme optimizasyonu.

---

## 14. Riskler ve Azaltma

| Risk | Etki | Azaltma |
|------|------|---------|
| Barge-in sırasında akustik yankı (kendi sesini duyma) | Yanlış kesme | Echo cancellation (AEC), TTS referans sinyaliyle filtreleme |
| Türkçe STT doğruluğu düşük | Kötü UX | Whisper large-v3 + Türkçe fine-tune, VAD ile temiz chunk |
| Uçtan uca gecikme yüksek | Doğallık kaybı | Streaming her katmanda, cümle bazlı TTS, GPU, vLLM |
| LLM halüsinasyonu | Yanlış bilgi | RAG + citation + "bilmiyorum" politikası |
| GPU maliyeti / kaynak | Ölçeklenme | Model kuantizasyonu (int8/4-bit), turbo modeller |

---

## 15. Açık Sorular
1. Hedef dağıtım ortamı: tam yerel (on-prem) mı, kendi bulut sunucumuz mu?
2. Bilgi tabanının kaynağı ve boyutu nedir (doküman sayısı)?
3. Ses klonlama (özel asistan sesi) gerekli mi, yoksa hazır ses yeterli mi?
4. Eşzamanlı kullanıcı sayısı hedefi (ölçekleme planı için)?

---

*Bu doküman yaşayan bir belgedir; teknik doğrulama (POC) ve benchmark sonuçlarına göre güncellenecektir.*
