# Kanal 1 — "How It Works" Shorts üretim sistemi

Sistemin tek doğruluk kaynağı [`CLAUDE.md`](CLAUDE.md). Kurulumun hangi aşamada olduğu [`KURULUM_DURUMU.md`](KURULUM_DURUMU.md) dosyasında.

## Windows'ta kurulum

Çalışma ortamı olarak Python sanal ortamı (venv) seçildi. Docker gerekmez.

1. **Python 3.11 veya üstü:** `winget install Python.Python.3.12`
2. **FFmpeg:** `winget install Gyan.FFmpeg` (kurulumdan sonra terminali kapatıp yeniden aç)
3. Repo klasöründe:
   ```powershell
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```
4. `.env` dosyasını Not Defteri ile aç ve API anahtarlarını yaz. `.env` GitHub'a gitmez.
5. Kontrol: `python -m core.healthcheck`. Altı satırın hepsi ✅ olmalı.
