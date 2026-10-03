# Kurulum durumu

Bölüm 15'teki aşamaların durumu. Yeni bir Claude Code oturumu buradan devam eder.

| Aşama | Durum | Not |
|---|---|---|
| 0 — Ortam ve anahtarlar | 🟡 Kısmen | FFmpeg ✅. `.env` şablonu ve `python -m core.healthcheck` hazır. API anahtarları bekleniyor. |
| 1 — API doğrulama ve fiyat tablosu | ⏳ Bekliyor | Anahtarlar ve ağ izni gerekiyor. |
| 2 — Çekirdek + veritabanı + maliyet | ⏳ Bekliyor | |
| 3 — Araştırma + senaryo | ⏳ Bekliyor | |
| 4 — Referans görsel sistemi | ⏳ Bekliyor | |
| 5 — Anahtar kareler + kare kalite kontrolü | ⏳ Bekliyor | |
| 6 — Pilot video | ⏳ Bekliyor | |
| 7 — İnceleme paneli + düzeltme | ⏳ Bekliyor | |
| 8 — Takvim, tampon, yükleme paketi, bildirim | ⏳ Bekliyor | |
| 9 — İlk parti | ⏳ Bekliyor | |
| 10 — Sürekli çalışma | ⏳ Bekliyor | |

## Kararlar

- Çalışma ortamı: Python venv (Docker değil). Windows adımları `README.md`'de.
- Video modu varsayılanı: hibrit (Bölüm 13). Aylık bütçe tavanı: 1000 $.
- LLM: `claude-opus-5-5` (config.yaml > llm.model).

## API anahtarları

| Değişken | Servis | Durum |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic | ⏳ |
| `FAL_KEY` | fal.ai | ⏳ |
| `GEMINI_API_KEY` | Google Gemini | ⏳ |
| `ELEVENLABS_API_KEY` | ElevenLabs | ⏳ |
| `PEXELS_API_KEY` | Pexels | ⏳ |
