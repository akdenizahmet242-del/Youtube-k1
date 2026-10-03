# KANAL 1 — "How It Works" Otomatik Shorts Üretim Sistemi
## Claude Code için tam kurulum talimatı

> **Ahmet için (bunu Claude Code'a vermeden önce oku):**
> 1. Boş bir klasör aç (ör. `C:\shorts-kanal1`). Bu dosyayı klasörün içine `CLAUDE.md` adıyla kaydet.
> 2. Claude Code'u bu klasörde başlat ve şunu yaz:
>    `CLAUDE.md dosyasını baştan sona oku. Bölüm 15'teki kurulum aşamalarını sırayla uygula. Her aşamanın sonunda kabul testlerini çalıştır, sonucu bana göster ve onayımı al. API anahtarlarını benden iste.`
> 3. Claude Code'un senden isteyeceği API anahtarları: **fal.ai** (video), **Google Gemini** (görsel), **ElevenLabs** (ses + efekt), **Anthropic** (senaryo + kalite kontrol), **Pexels** (referans fotoğraf, ücretsiz).

---

## 0. Claude Code'a not: bu belge nasıl okunmalı

- Bu belge, sistemin **tek doğruluk kaynağıdır**. Bir kural ile bir kolaylık çatışırsa **kural kazanır**.
- **Bölüm 2'deki kurallar pazarlık konusu değildir.** Her pipeline adımında kontrol edilir.
- API'ler hızla değişir. Kurulumda kullanacağın her API'nin (fal.ai Seedance 2.5, Gemini 3 Pro Image, ElevenLabs) **güncel dokümantasyonunu oku**, parametre adlarını ve fiyatları doğrula. Bu belgedeki parametreler Ekim 2026 itibarıyla doğrulanmıştır, ama yine de kontrol et.
- Kullanıcı (Ahmet) Türkçe konuşur, videolar **İngilizce**dir. Kullanıcıya gösterilen her şey (inceleme paneli, raporlar, hata mesajları) **Türkçe**; videoya giren her şey (seslendirme, altyazı, ekran yazıları, başlık, açıklama) **İngilizce** olmalı.
- Emin olmadığın bir tasarım kararında **kullanıcıya sor**, varsayımla ilerleme.
- Bu sistem önce **yalnızca Kanal 1** için kurulur. Ama kod, ileride Kanal 2 ve 3'ün sadece yeni bir `channels/<kanal>.yaml` dosyası ve prompt seti ile eklenebileceği şekilde yazılmalı (kanal-bağımsız çekirdek + kanal-özel yapılandırma).

---

## 1. Proje özeti

**Kanal:** İngilizce, global kitleye yönelik YouTube Shorts kanalı. Konu: makinelerin ve cihazların **nasıl çalıştığı** (dizel motor, işlemci, klima, televizyon, buzdolabı, jet motoru...).

**Amaç:** Her gün 2 Short yayınlamak. Videolar tamamen yapay zekâ ve otomasyonla üretilir. Ahmet yalnızca **kontrol eder**, gerekirse **düzeltme ister** ve beğendiklerini **kendisi elle yükler**. YouTube'a otomatik yükleme **yapılmayacak**.

**Kalite çıtası:** Fotogerçekçi, sinematik, kesintisiz kamera hareketli, teknik olarak **doğru** videolar. Yapay zekânın "kafasından uydurduğu" mantıksız makineler kesinlikle kabul edilmez. Her görsel, gerçek referans görsellere dayanır.

---

## 2. Değişmez kurallar (her adımda kontrol edilir)

| # | Kural | Nasıl uygulanır |
|---|---|---|
| 1 | **Videolarda kadın olmaz.** | Varsayılan: videoda **hiç insan olmaz**. Bir sahnede insan zorunluysa (ör. sürücü), yalnızca yetişkin erkek; yüz net görünmez. Her görsel/video promptunun yasak listesinde yer alır. Otomatik kalite kontrolü (Bölüm 9) her videoda kare kare kontrol eder. İhlal = video otomatik reddedilir. |
| 2 | **Videolarda müzik olmaz.** | Video modellerinde ses üretimi **kapalı** (`generate_audio: false`). Modelden gelen her ses izi **silinir**. Ses yalnızca: İngilizce erkek anlatıcı + gerçekçi mekanik ses efektleri (SFX). Ses efekti üretim promptlarına "no music, no melody, no instruments" eklenir. Son ses kontrolü müzik algılarsa video reddedilir. |
| 3 | **Format: YouTube Shorts.** | Dikey 9:16, çıktı 1080×1920, 30 fps, H.264 + AAC. Süre **30–55 saniye** (hedef ~45 sn). Başlangıç ve bitiş kareleri döngü (loop) için uyumlu. |
| 4 | **Promptlar aşırı ayrıntılı olur.** | Her sahne promptu Bölüm 7'deki 9 başlıklı şablonu **eksiksiz** doldurur: ne görünür, kaç parça, hangi malzeme, hangi renk, hangi yöne hareket, kamera nereden nereye, hangi hızla, ne yasak. "Bir motor" gibi kısa promptlar **yasaktır**. Amaç: ilk denemede doğru sonuç. |
| 5 | **Günde 2 video, 1 hafta önden.** | Yayın takvimi her zaman **en az 14 onaylı video** (7 gün × 2) önde olmalı. İnceleme ve düzeltme bölümü (Bölüm 10) ayrıntılı kurulur. |
| 6 | **Her video referans görsellerle üretilir.** | Konuyla ilgili gerçek fotoğraflar ve kesit görselleri toplanır (Bölüm 6). Bu referanslardan önce **anahtar kareler** (keyframe) üretilir, onaylanır, sonra videoya çevrilir. Model hiçbir makineyi hayal gücünden üretmez. |
| 7 | **Otomasyon + insan kontrolü.** | Konu seçiminden montaja kadar her şey otomatik. Ahmet yalnızca inceleme panelinde izler, onaylar ya da düzeltme ister. Yükleme elle yapılır; sistem yükleme paketi (video + başlık + açıklama + etiketler) hazırlar. |
| 8 | **Tam zincir anlatımı.** | Video yalnızca mekanizmayı anlatıp bitmez. **"Sonra ne oluyor?"** sorusu, son kullanıcının gördüğü sonuca kadar sorulur. Örnek: motor yakar → piston iter → krank döner → şanzıman → aks → teker döner → **araba gider**. Bölüm 3. |

Ek kurallar:
- **Marka ve logo yok.** Arabalar, işlemciler ve cihazlar markasız, jenerik tasarımda olur. Görünür yazı, rozet ya da plaka olmaz. Plaka gerekiyorsa boş olur.
- **Yanlış bilgi yok.** Her teknik iddia araştırma adımında bir kaynakla eşleşir (Bölüm 5, Adım 2). Kaynaksız iddia senaryoya giremez.
- **Kan, yaralanma, kaza, felaket görüntüsü yok** (reklam uygunluğu).
- **Yapay zekâ ile üretildiğini gizleme yok.** Yükleme paketinde, YouTube'daki "altered or synthetic content" (değiştirilmiş veya sentetik içerik) etiketinin işaretlenmesi hatırlatılır.

---

## 3. Video formatı: "Dışarıdan İçeriye + Tam Zincir"

Her video, aşağıdaki **6 vuruşlu iskeleti** izler. Sert kesme **yok**: geçişler kesintisiz kamera hareketidir. Bunu sağlamak için her sahnenin **son karesi**, bir sonraki sahnenin **ilk karesidir** (bkz. Bölüm 5, Adım 5–7).

| Vuruş | Süre | Ne olur | Kamera |
|---|---|---|---|
| 1. Gerçek dünyada dışarıdan kanca | 0–6 sn | Cihaz kendi doğal ortamında çalışırken görünür (araba yolda gider, klima duvarda çalışır, bilgisayar açık). Anlatıcı şaşırtıcı ama **doğru** bir soru sorar. | Yavaş yörünge (soldan sağa ya da sağdan sola), alçak sinematik açı |
| 2. Cihaza yaklaşma | 6–10 sn | Kamera cihaza yaklaşır, ilgili bölgeye odaklanır (kaput, kasa, gövde). | Kesintisiz ileri hareket (dolly-in) |
| 3. İçeri dalış | 10–14 sn | Dış kabuk saydamlaşır ya da kesit düzlemi kayar. Gerçek iç yapı görünür. | Yüzeyin içinden geçen ileri hareket |
| 4. Mekanizma | 14–34 sn | Çalışma prensibi adım adım. Her adım tek, yumuşak bir kamera hareketi. Üstte adım etiketi, sağ üstte tek bir sayı. | Adımlar arası yumuşak kaydırma ve yakınlaşma |
| 5. Tam zincir: "sonra ne oluyor?" | 34–42 sn | Üretilen iş, son kullanıcının gördüğü sonuca kadar takip edilir (krank → şanzıman → aks → teker; işlemci → ekranda görüntü; klima → odaya soğuk hava). | Enerji/sinyal yolunu takip eden kamera |
| 6. Dışarı çıkış + döngü | 42–46 sn | Kamera geri çekilir, kabuk kapanır, cihaz gerçek dünyada sonucu üretir (araba hızlanıp uzaklaşır). Son kare, ilk kareye benzer. | Geri çekilme, ilk açıya dönüş |

**Ekran dili (her videoda aynı):**
- **Altyazı:** Alt-orta bölgede (alttan ~430 px yukarıda; Shorts arayüzünün altında kalmaz), kalın, beyaz, siyah gölgeli. Söylenen kelime **amber (#FFC04D)** renkte yanar. En fazla 6 kelime / 2 satır.
- **Adım etiketi:** Sol üstte (üstten ~150 px), ör. `STROKE 02 / 04` + `COMPRESSION`, altında ilerleme çubuğu.
- **Sayı göstergesi (HUD):** Sağ üstte tek bir sayı, ör. `520°C`, `20:1`. Ekranda aynı anda en fazla bir sayı.
- **Yazı tipi:** Inter (ExtraBold / Bold).
- **Görsel stil:** Fotogerçekçi, stüdyo ışığı. İç kesit görünümlerinde kesilen yüzeyler **turuncu (#FF7A1A)**. Hava mavi, ısınan hava turuncu, yakıt sarı, yanma beyaz-sarı-turuncu, egzoz gri. Bu renk kodu tüm kanalda sabittir.

**Ses dili:**
- Anlatıcı: ElevenLabs, derin ve net, enerjik bir **erkek** sesi (sabit `voice_id`, config'de). Hız ~165–175 kelime/dakika.
- Ses efektleri: harekete senkron, gerçekçi (motor rölantisi, emme hışırtısı, enjektör "tss", ateşleme gümbürtüsü, egzoz, dişli ve kayış sesleri). **Müzik asla yok.**
- Ses seviyesi: son mikste -14 LUFS, anlatıcı efektlerin 8–10 dB üstünde.

---

## 4. Araçlar ve servisler

| İş | Araç | Not |
|---|---|---|
| Video (sahne sahne) | **Seedance 2.5** (fal.ai üzerinden) | Kullanılacak endpoint: `bytedance/seedance-2.5/image-to-video`. Parametreler: `image_url` (ilk kare), `end_image_url` (son kare), `prompt`, `duration` ("4"–"30"), `aspect_ratio` "9:16", `resolution` "720p" (veya bütçe modu "480p"), **`generate_audio: false`**, `seed`. Alternatif endpoint: `bytedance/seedance-2.5/reference-to-video` (en fazla 50 referans, promptta `[Image1]` gibi etiketlerle). Fiyat (fal.ai, Ekim 2026): 720p ≈ 0,47 $/sn, 480p ≈ 0,22 $/sn. **Kurulumda doğrula.** |
| Anahtar kareler (keyframe) | **Nano Banana Pro** (Google Gemini API, model `gemini-3-pro-image`) | En fazla 14 girdi görseli (6 nesne referansı + 3 stil referansı dahil). `aspect_ratio` "9:16", `image_size` "2K". Fiyat ≈ 0,13 $/görsel (2K). **Kurulumda doğrula.** |
| Araştırma, senaryo, sahne listesi, kalite kontrol, düzeltme yorumlama | **Claude API** (Anthropic; güncel en iyi Sonnet ya da Opus modeli, görsel girdi destekli). Web araştırması için Claude'un web arama aracı. | Tüm LLM çağrıları JSON şemasıyla doğrulanır. |
| Seslendirme | **ElevenLabs** TTS, **zaman damgalı** (with-timestamps) uç noktası | Kelime düzeyinde zaman damgası = altyazı senkronu. |
| Ses efektleri | **ElevenLabs Sound Effects** API (yedek: lisanslı SFX kütüphanesi) | Promptlara her zaman "no music" eklenir. |
| Referans görseller | **Wikimedia Commons API**, **Openverse API**, **Pexels API** (lisanslı, ücretsiz). İsteğe bağlı: Google Görseller (SerpAPI ile, yalnızca iç referans). | Bölüm 6. |
| Montaj | **FFmpeg** (birleştirme, ölçekleme, ASS altyazı, ses miksi, loudnorm) | Altyazıda kelime vurgusu: ASS karaoke etiketleri (`\k`) ya da kelime başına ayrı olay. |
| Orkestrasyon | **Python 3.11+**, SQLite, iş kuyruğu (APScheduler ya da basit worker döngüsü) | n8n zorunlu değil. Ahmet isterse n8n yalnızca tetikleyici olarak eklenebilir. |
| İnceleme paneli | **FastAPI + basit HTML/JS** (yerel, `http://localhost:8080`) | Bölüm 10. |
| Çalışma ortamı | Ahmet'in Windows bilgisayarı (Docker Desktop mevcut) | Docker Compose ile ya da doğrudan Python venv ile. Kurulumda Ahmet'e sor. |

**Neden "önce anahtar kare, sonra video"?**
Video modeline doğrudan "dizel motor" dendiğinde, model kafasından bir motor uydurur ve parçalar saçmalaşır. Bunun yerine:
1. Gerçek referans fotoğraflar toplanır.
2. Bu referanslardan Nano Banana Pro ile **sahnelerin başlangıç ve bitiş kareleri** üretilir.
3. Bu kareler otomatik olarak ve gerekirse Ahmet tarafından kontrol edilir. Kare üretmek ucuzdur (~0,13 $), video pahalıdır (~2–4 $/sahne).
4. Seedance, bu iki kare arasını videoya çevirir.

Böylece motorun görünüşü referanslara bağlı kalır. Ardışık sahneler ortak kareyi paylaştığı için geçişler kesintisiz olur.

---

## 5. Pipeline: adım adım

Her video bir `job` kaydıdır. Durumları sırayla şöyle ilerler:

`queued → researching → scripted → refs_ready → keyframes_ready → voiced → shots_ready → assembled → auto_qc_passed → awaiting_review → (approved | needs_revision | rejected) → scheduled → published`

Her adım **idempotent** olmalı: tekrar çalıştırıldığında var olan çıktıyı yeniden kullanır, yalnızca eksik ya da geçersiz olanı üretir. Her adımın girdisi, çıktısı, maliyeti, süresi ve hataları `jobs/<job_id>/log.jsonl` dosyasına yazılır.

### Adım 1 — Konu seçimi
- Kaynak: `channels/k1/ideas.yaml` (Bölüm 16'daki liste ile başlatılır).
- Her fikirde: `id`, `title`, `device`, `real_world_context` (dış sahne), `mechanism`, `chain_to_result` (tam zincir), `hook_question`, `status`.
- Planlayıcı, tampon hedefini (Bölüm 11) karşılayacak kadar fikri `queued` yapar. Aynı cihaz türü arka arkaya iki gün yayınlanmaz.

### Adım 2 — Araştırma (`facts.json`)
- Claude, web aramasıyla konuyu araştırır ve **doğrulanmış gerçekler listesi** çıkarır. Her gerçekte: `claim`, `value` (varsa sayı ve birim), `source_url`, `source_title`, `confidence`.
- Sayılar en az **iki bağımsız kaynakla** doğrulanır. Doğrulanamayan sayı ya kullanılmaz ya da "about / up to" gibi güvenli bir ifadeyle yazılır.
- Ayrıca cihazın **gerçek bileşen listesi** çıkarılır: parça adları, sayıları, yerleşimi, hareket yönleri ve sıralaması. Bu liste, görsel promptlarının temelidir. Ör. dizel motor: 4 silindir sıralı, her silindirde 2 emme + 2 egzoz supabı, ortada enjektör, piston tepesinde yanma odası çanağı, turbo, egzoz manifoldu, krank, volan.

### Adım 3 — Senaryo ve sahne listesi (`script.json`)
- Bölüm 7.2'deki **Senaryo Planlayıcı Prompt** kullanılır. Çıktı Bölüm 14'teki JSON şemasına uymalıdır.
- 6 vuruşlu iskelet (Bölüm 3) zorunludur. Toplam **8–11 sahne** olur, sahne başına 3–7 saniye.
- Her sahne için: anlatım metni, ilk kare tarifi, son kare tarifi, kamera hareketi, hareket eden her parça, adım etiketi, HUD sayısı, SFX listesi, kullanılacak referans görsel etiketleri.
- Anlatım: toplam 100–130 kelime, cümleler 12 kelimeden kısa, kancada soru, sonunda sonuç cümlesi.

### Adım 4 — Referans görseller (`refs/`)
Bölüm 6'ya göre toplanır, puanlanır ve sahnelere atanır.

### Adım 5 — Anahtar kareler (`keyframes/K00.png … K{N}.png`)
- N sahne için **N+1 anahtar kare** gerekir. Sahne *i*, `K(i-1)` ile başlar ve `K(i)` ile biter.
- Kareler **sırayla** üretilir. Her kare üretilirken şunlar verilir:
  - Sahneye atanmış **nesne referansları** (en fazla 6; gerçek fotoğraflar ve kesit görselleri).
  - **Stil referansları** (en fazla 3): bir önceki onaylı anahtar kare + kanalın sabit stil örnekleri (`channels/k1/style_refs/`).
  - Bölüm 7.3'teki şablonla yazılmış **ayrıntılı kare promptu**.
- Her kare **Görsel Kalite Kontrol Promptu** (Bölüm 7.6) ile denetlenir: referansa uygunluk, parça sayısı, fiziksel mantık, insan/kadın yokluğu, yazı/logo yokluğu, 9:16 kadraj. 10 üzerinden puan 8'in altındaysa kare yeniden üretilir (en fazla 3 deneme). Yine geçmezse job `needs_attention` durumuna düşer ve Ahmet'e bildirilir.
- Kare boyutu: 9:16, 2K. Video üretimine giderken 720p'ye uygun ölçeklenir.

### Adım 6 — Seslendirme (`audio/voice.mp3` + `audio/words.json`)
- ElevenLabs zaman damgalı TTS. Her sahnenin anlatım metni ayrı parça olarak ya da tek parça halinde üretilip sahne sınırlarına göre bölünür.
- **Sahne süreleri seslendirmeye göre ayarlanır:** sahne süresi = o sahnenin anlatım süresi + 0,2–0,4 sn. Bu süre, Seedance'in kabul ettiği tam saniyeye yukarı yuvarlanır (en az 4 sn). Montajda tam süreye kırpılır.

### Adım 7 — Video sahneleri (`shots/S01.mp4 …`)
- Her sahne için Seedance image-to-video çağrılır: `image_url = K(i-1)`, `end_image_url = K(i)`, `prompt` = Bölüm 7.4 şablonu, `aspect_ratio "9:16"`, `generate_audio false`, `duration` = Adım 6'dan gelen süre, `seed` kaydedilir.
- Sahneler paralel üretilebilir; aynı anda en fazla `max_concurrent_video_jobs` (config, varsayılan 3).
- Her sahne, Bölüm 9'daki sahne kontrolünden geçer. Başarısız sahne en fazla 2 kez yeniden üretilir (yeni seed + kontrol notlarıyla güçlendirilmiş prompt).

### Adım 8 — Ses efektleri (`audio/sfx_*.wav`)
- Sahne listesindeki her SFX olayı için ElevenLabs Sound Effects ile kısa efekt üretilir ya da önbellekteki kütüphaneden kullanılır. Sık efektler (rölanti, kayış, enjektör) bir kere üretilir ve `assets/sfx_cache/` içinde tekrar kullanılır.
- Her efekt promptunun sonuna şu eklenir: `realistic mechanical sound only, no music, no melody, no instruments, no voice`.

### Adım 9 — Montaj (`final/<job_id>.mp4`)
1. Sahneleri sırayla birleştir. Ortak kare nedeniyle sert kesme oluşmaz; ek geçiş efekti **kullanma**. Gerekirse ek noktasında 2–4 karelik çapraz geçiş.
2. 1080×1920'ye ölçekle (lanczos). İsteğe bağlı: yapay zekâ ile netlik artırma.
3. Altyazıyı ASS olarak bindir: kelime kelime amber vurgu, en fazla 2 satır.
4. Adım etiketlerini ve HUD sayılarını ASS katmanı olarak ekle, yumuşak giriş ve çıkışla (0,3 sn).
5. Ses: anlatıcı + SFX. Videodan gelebilecek her ses izi atılır. `loudnorm` ile -14 LUFS, tepe -1 dBTP.
6. Kapak karesi (thumbnail): kancanın en çarpıcı karesinden bir PNG.

### Adım 10 — Otomatik kalite kontrolü
Bölüm 9.

### Adım 11 — İnceleme, düzeltme, onay
Bölüm 10.

### Adım 12 — Yükleme paketi ve takvim
Bölüm 11–12.

---

## 6. Referans görsel sistemi

**Amaç:** Modelin gerçek parçaları, oranları ve yerleşimi görmesi. Referansın birebir kopyası çizilmez; referanslar **doğruluk ve görünüş rehberi**dir.

**Her video için toplanacak referans kategorileri** (sahne listesinden otomatik çıkarılır):
1. **Dış görünüş:** cihazın gerçek hayattaki hali (ör. modern SUV dış çekim, motor bölmesi kaput açık).
2. **Montajlı bileşen:** ör. motor bölmesindeki dizel motor, turbo, manifold.
3. **Kesit / cutaway:** müze tipi kesilmiş motor fotoğrafları, teknik kesit illüstrasyonları (iç yapının doğruluğu için kritik).
4. **Detay parçalar:** piston, biyel, krank mili, enjektör, supap, volan, şanzıman.
5. **Zincirin devamı:** şanzıman, kardan mili, diferansiyel, aks, teker.

**Arama sırası** (lisans güvenliğine göre):
1. Wikimedia Commons API: ticari kullanıma uygun lisanslar (CC0, CC BY, CC BY-SA, Public Domain). Lisans ve yazar bilgisi kaydedilir.
2. Openverse API (ticari kullanım filtresiyle).
3. Pexels API.
4. **İsteğe bağlı**, config ile açılıp kapanır: Google Görseller (SerpAPI). Bu görseller **yalnızca iç referans** olarak modele verilir. Hiçbir koşulda videoya ya da kapağa doğrudan girmez. Kaynak URL'leri kaydedilir. Telif hakkı riskini azaltmak için varsayılan **kapalı**dır. Ahmet açmak isterse onaylatılır.

**Seçim ve puanlama:**
- Her kategori için 15–30 aday indirilir. Claude görsel girdiyle her adayı puanlar (0–10): konuyla alaka, teknik doğruluk, netlik, filigran/yazı/logo yokluğu, insan yokluğu.
- Sahne başına en iyi 3–6 referans seçilir ve `refs/manifest.json` dosyasına yazılır: `ref_id`, `category`, `local_path`, `source_url`, `license`, `author`, `score`, `assigned_shots`.
- Kanal genelinde yeniden kullanılabilir referans kütüphanesi tutulur: `assets/ref_library/<cihaz>/`. Aynı cihaz tekrar işlendiğinde önce kütüphaneye bakılır.

**Stil referansları:** `channels/k1/style_refs/` klasöründe, Ahmet'in onayladığı 3–5 "altın standart" kare tutulur (ışık, renk, turuncu kesit stili). Pilot videodan sonra bu klasör, onaylanan en iyi karelerle doldurulur. Her yeni karede stil referansı olarak verilir. Böylece kanalın görünüşü sabit kalır.

---

## 7. Prompt sistemi

Tüm promptlar `channels/k1/prompts/` klasöründe ayrı dosyalarda tutulur ve sürümlenir. Kod içine gömülmez.

### 7.1 Değişmez yasak listesi (her görsel ve video promptunun sonuna eklenir)

```
STRICTLY FORBIDDEN: any woman or girl; any human face; any text, letters, numbers, labels, watermarks, logos, brand names, badges or license plate characters; cartoon or toy look; extra or missing mechanical parts; parts passing through each other; melting or morphing geometry; blood or injury; music notes; split screens; hard cuts.
```

### 7.2 Senaryo Planlayıcı Prompt (Claude, çıktı JSON)

```
You are the lead writer and director of "How It Works", a photoreal YouTube Shorts channel.
Plan ONE vertical 9:16 Short, 40-50 seconds, English narration, for this topic:
TOPIC: {title}
DEVICE: {device}
REAL-WORLD CONTEXT (opening exterior scene): {real_world_context}
MECHANISM: {mechanism}
FULL CHAIN TO THE END RESULT: {chain_to_result}
VERIFIED FACTS (use only these numbers and claims): {facts_json}
COMPONENT LIST (real parts, counts, positions, motions): {components_json}

Mandatory structure: 6 beats, in this order, no hard cuts, every transition is a continuous camera move:
1 EXTERIOR HOOK (0-6s): the device working in its real environment. Camera slow orbit. Narration: one surprising and TRUE question.
2 APPROACH (about 4s): continuous dolly-in toward the relevant area.
3 DIVE INSIDE (about 4s): the outer shell turns transparent or a section plane slides through it. Cut faces are solid orange.
4 MECHANISM (about 20s): 3-5 steps in physically correct order. Each step: one smooth camera move, one on-screen step label, at most one HUD number.
5 FULL CHAIN (about 8s): keep asking "and then what?" until the result a normal person sees (for example: crankshaft -> gearbox -> driveshaft -> wheels turn).
6 PULL OUT AND LOOP (about 4s): camera returns outside. The device produces its visible real-world result. The last frame resembles the first frame.

Rules:
- 8 to 11 shots, 3 to 7 seconds each. Shot i starts exactly on the end frame of shot i-1.
- Narration: 100-130 words total, sentences under 12 words, no filler, no "in this video".
- Every factual claim must map to a fact id from VERIFIED FACTS.
- No people at all. If a person is unavoidable, an adult man with his face not visible. Never a woman.
- No brand names, no logos, no readable text in the images.
- No music. Sound = narration + realistic mechanical sound effects only.
- For EVERY shot write: start_frame and end_frame descriptions so precise that two different artists would draw the same image (list every visible part, its count, material, color, position, state; camera position, height, angle, lens). Write camera_move (start position, path, end position, speed, easing). Write motion (every moving part, direction, speed, order of events). Also write overlay_label, hud, sfx[], refs_needed[] (reference categories), and the fact_ids used.

Return ONLY JSON matching the provided schema.
```

### 7.3 Anahtar Kare Promptu şablonu (Nano Banana Pro)

Her kare promptu **9 başlığın tamamını** doldurur:

```
[1 PURPOSE] Keyframe {Kxx} of a photoreal vertical 9:16 technical Short. This is the {start|end} frame of shot {Sxx}: "{shot title}".
[2 REFERENCES] Use the attached images as ground truth for shape, proportions and part layout:
  Image 1 = {ref description, e.g. "real inline-4 turbo-diesel engine in an SUV engine bay, top view"}
  Image 2 = {...}
  Style images = channel look (lighting, colors, orange section faces). Match their look, not their content.
  Do NOT copy any reference literally. Do NOT invent parts that the references and the component list do not show.
[3 SUBJECT] {every visible part: name, count, material, finish, color, size relative to frame, exact position (left/right/top/bottom, foreground/background), current state, e.g. "piston at bottom dead center, both intake valves open 8 mm, exhaust valves closed"}
[4 COMPOSITION] Camera position {x/height}, angle {e.g. 15 degrees above, looking down the cylinder axis}, lens {e.g. 35 mm equivalent}, framing {subject fills the central 60% of frame, top 15% and bottom 25% kept calm for on-screen text}.
[5 LIGHTING] Studio key light from upper left, warm 4500K; cool rim light from back right; soft reflections on metal; dark charcoal background #15171B with subtle gradient. In cutaway frames, combustion areas glow from inside.
[6 MATERIALS & COLOR CODE] Cast iron block dark grey; aluminium head and pistons light silver; forged steel crank dark steel; section faces solid orange #FF7A1A; air particles light blue; heated air orange; diesel spray yellow; combustion white-yellow-orange; exhaust grey.
[7 CONTINUITY] Must match the previous keyframe {Kxx-1} exactly in camera, lighting and part design (attached as style image).
[8 PHOTOREALISM] Photoreal 3D render quality, physically accurate, sharp focus on subject, shallow depth of field in background only, no cartoon style.
[9 FORBIDDEN] {Bölüm 7.1 listesinin tamamı}
```

### 7.4 Video Sahne Promptu şablonu (Seedance image-to-video)

```
[SHOT] {Sxx} of {N}, {duration}s, vertical 9:16, photoreal, continuous single take, no cuts.
[START] The video begins exactly on the provided first frame: {1-sentence summary of Kxx-1}.
[END] The video ends exactly on the provided last frame: {1-sentence summary of Kxx}.
[CAMERA] {start position} -> {path, e.g. "slow dolly-in along the cylinder axis, 30 cm, no rotation"} -> {end position}. Speed: {slow|medium}, smooth ease-in-out, no shake {unless ignition: "one short subtle shake at second 1.2"}.
[MOTION — in this exact order]
  0.0-{t}s: {part} moves {direction} at {speed}; {other parts} stay still.
  {t}-{t2}s: ...
  Physically correct: crankshaft rotates {direction}; piston motion follows crank angle; valves open only during {stroke}.
[PARTICLES/EFFECTS] {air/fuel/flame/exhaust behaviour, colors per color code}
[KEEP CONSTANT] Same engine design, part count, materials, lighting and background as the first and last frame. Nothing appears or disappears unless stated.
[FORBIDDEN] {Bölüm 7.1 listesinin tamamı}
```

### 7.5 Ses efekti promptu şablonu (ElevenLabs SFX)
```
{event}, {material}, {distance: close-up|medium}, {duration}s, realistic mechanical sound only, no music, no melody, no instruments, no voice.
```

### 7.6 Görsel Kalite Kontrol Promptu (Claude, görsel girdili, çıktı JSON)
```
You are a strict technical QA reviewer for a photoreal "How It Works" Short.
Inputs: the candidate image (or video frames sampled at 2 fps), the reference images, the component list, and the shot description.
Score 0-10 and list problems for each check:
1 technical_accuracy: parts, counts, positions and motion are consistent with the references and the component list; nothing invented.
2 physical_logic: no parts intersecting, floating or morphing; motion order is physically correct.
3 continuity: matches the previous frame or shot in design, lighting and camera.
4 people: is ANY person visible? Is ANY woman or girl visible? (any woman = automatic fail)
5 text_logos: any readable text, letters, logos, badges, watermark? (any = fail)
6 realism: photoreal, not cartoon or toy-like.
7 composition: 9:16; key action in the central area; top 15% and bottom 25% calm for text overlays.
Return JSON: {"pass": bool, "scores": {...}, "fatal": [...], "problems": [...], "fix_instructions": "precise prompt changes to fix the problems"}
Pass only if no fatal issue and every score >= 8.
```

### 7.7 Düzeltme Yorumlayıcı Prompt (Claude, çıktı JSON)
```
The reviewer (Ahmet) wrote revision notes in Turkish for video {job_id}. Notes may reference timestamps (e.g. "0:12'deki piston yanlış") or shots (e.g. "S04") or the whole video.
Map every note to the exact affected items: shot ids, keyframe ids, narration lines, captions, HUD, SFX, title/description.
For each affected item, output the precise change: new prompt text (full, not a diff), new narration text, or new overlay text.
Regenerate the minimum set: if a keyframe changes, both shots that use it must be regenerated; if narration timing changes, recompute shot durations.
Keep everything Ahmet did not mention unchanged.
Return JSON: {"changes":[{"target":"K05|S04|narration:S04|caption|hud:S06|sfx:S07|meta:title","reason":"...","new_value":"..."}],"regenerate":{"keyframes":[...],"shots":[...],"voice":bool,"assembly":true},"questions_for_ahmet":[...]}
If a note is ambiguous, put a question in questions_for_ahmet instead of guessing.
```

---

## 8. Altın standart örnek: "How a diesel engine moves a car"

Bu örnek, kalite çıtasını gösterir. Senaryo planlayıcı, ilk çalıştırmalarda bu örneği **few-shot örneği** olarak alır. Pilot video (Bölüm 15, Aşama 6) bu konu ile üretilir.

**Anlatım (~115 kelime):**
> "This SUV has no spark plugs. So how does it burn its fuel? Let's look under the hood. First, the piston slides down and pulls in air. Only air. Then it squeezes that air about twenty times smaller. Squeezed that hard, the air gets hotter than five hundred degrees. Now a fine mist of diesel sprays in, and it ignites on its own. No spark needed. The blast drives the piston down and spins the crankshaft. Then the piston rises and pushes the exhaust out. Four cylinders take turns, dozens of times every second. That spinning crankshaft drives the gearbox, the driveshaft and finally the wheels. And that's how a few drops of fuel move two tons of steel."

(Her sayı araştırma adımında doğrulanmalı: sıkıştırma oranı ~15–20:1, sıkıştırma sonu hava sıcaklığı >500 °C, orta boy SUV ~2 ton.)

**Sahne listesi (özet; gerçek çıktıda her alan Bölüm 7.3–7.4 şablonlarıyla tam doldurulur):**

| Sahne | Süre | İlk kare → son kare | Kamera | Hareket | Etiket / HUD | SFX |
|---|---|---|---|---|---|---|
| S01 | 0–5 sn | K00: markasız koyu gri orta boy SUV, boş sahil yolunda gün batımında sürüyor, sol-ön alçak açı. Camlar koyu, içerisi görünmüyor, plaka boş → K01: aynı araba, sağ-ön 3/4 açı | Alçak yörünge, soldan sağa, aracın hızına eşlik eder | Tekerler döner, araba sabit hızda ilerler | Başlık "HOW IT WORKS / DIESEL ENGINE" | Dizel motor sürüş sesi, yol uğultusu |
| S02 | 5–9 sn | K01 → K02: araba yol kenarında durmuş, rölantide; kamera kaputun 1 m önünde, kaputa bakıyor | Kesintisiz yaklaşma, kaputa doğru alçalma | Araba yavaşlayıp durur, gövde hafifçe titrer (rölanti) | — | Rölanti |
| S03 | 9–13 sn | K02 → K03: kaput yarı saydamlaşmış, altında gerçekçi sıralı 4 silindir turbo dizel motor (motor kapağı, turbo, manifold) | Kaputun içinden geçen ileri hareket, 20° yukarıdan | Kaput saydamlaşır; motorda kayış ve kasnak döner | — | Hafif "whoosh" + rölanti |
| S04 | 13–17 sn | K03 → K04: motorun ön yarısını kesen dikey kesit düzlemi; 4. silindir ortadan kesik, kesik yüzeyler turuncu; piston, biyel, krank, supaplar görünür | Motor bloğunun yan tarafına kayıp kesit düzlemine bakma | Kesit düzlemi soldan sağa kayar | — | Metal kesme değil, yumuşak geçiş sesi |
| S05 | 17–21 sn | K04 → K05: piston aşağıda (alt ölü nokta), 2 emme supabı açık, silindir mavi hava parçacıklarıyla dolu | Kesite yavaş yaklaşma | Piston aşağı iner, emme supapları açılır, mavi hava emme kanalından akar | STROKE 01/04 INTAKE | Emme hışırtısı |
| S06 | 21–26 sn | K05 → K06: piston üstte (üst ölü nokta), tüm supaplar kapalı, sıkışmış hava turuncu parlıyor | Yanma odasına yakın plan | Piston yükselir, parçacıklar sıkışır, maviden turuncuya döner | 02/04 COMPRESSION · HUD 520°C | Yükselen basınç tonu |
| S07 | 26–30 sn | K06 → K07: enjektörden 6 ince sarı yakıt jeti, yanma beyaz-sarı parıltı | Enjektör ucuna yakın plan, son anda hafif sarsıntı | Yakıt jetleri büyür → anında tutuşma, parlama | 03/04 POWER | Enjektör "tss" + boğuk patlama |
| S08 | 30–34 sn | K07 → K08: piston aşağıda, biyel aşağı itilmiş, krank dönmüş; kamera krank seviyesinde | Biyel boyunca aşağı takip eden kamera | Piston aşağı itilir, biyel krankı döndürür | 03/04 POWER | Mekanik gümbürtü |
| S09 | 34–37 sn | K08 → K09: piston yukarıda, egzoz supapları açık, gri gaz egzoz kanalından çıkıyor | Egzoz tarafına kayma | Piston yükselir, gri gaz dışarı itilir | 04/04 EXHAUST | Egzoz "puf" |
| S10 | 37–42 sn | K09 → K10: x-ray araç görünümü; krank → volan → şanzıman → kardan mili → diferansiyel → arka tekerler; güç yolu turuncu ışık akışıyla gösteriliyor | Motordan arka tekerleğe, aracın altında kayan kamera | Turuncu enerji akışı zincir boyunca ilerler, tüm mil ve dişliler döner, teker dönmeye başlar | "CRANKSHAFT → GEARBOX → WHEELS" | Dişli ve mil uğultusu |
| S11 | 42–46 sn | K10 → K11 (≈K00): x-ray kapanır, araba yoldan hızlanarak uzaklaşır, sol-ön alçak açı | Geri çekilme + yörünge, ilk açıya dönüş | Araba hızlanır | HUD "~2 TONS" | Hızlanma sesi |

**Örnek tam kare promptu (K05, S05'in son karesi):**
```
[1 PURPOSE] Keyframe K05 of a photoreal vertical 9:16 technical Short. End frame of shot S05 "Intake stroke".
[2 REFERENCES] Image 1 = museum cutaway of a modern inline-4 turbo-diesel engine, cylinder section visible. Image 2 = close photo of a diesel piston with combustion bowl in the crown and three piston rings. Image 3 = cylinder head cutaway showing 2 intake and 2 exhaust valves per cylinder and a central vertical injector. Style images = channel look + previous keyframe K04. Do not copy references literally; do not invent parts not shown in them.
[3 SUBJECT] Vertical section through cylinder 4 of an inline-4 turbo-diesel engine. Cut faces of the block and head are solid orange. Visible inside the section: one cylinder bore with polished steel liner; aluminium piston at bottom dead center with a shallow bowl in its crown and three dark rings; connecting rod angled slightly to the right down to the crankshaft; crankshaft counterweight below. In the head: two intake valves on the LEFT side, open about 8 mm; two exhaust valves on the RIGHT side, fully closed; one vertical injector exactly in the center between the valves, tip just visible at the roof of the chamber. The intake port on the left is filled with a stream of small light-blue air particles flowing into the cylinder. The cylinder volume above the piston is evenly filled with light-blue air particles. The exhaust port on the right is empty and dark.
[4 COMPOSITION] Camera 1.6 m from the section plane, at piston-crown height, looking straight at the cut, 35 mm lens. The cylinder fills the central 55% of the frame. Valves and injector in the upper third. Crankshaft at the lower edge. Top 15% and bottom 25% are calm, dark areas.
[5 LIGHTING] Warm key light from upper left, cool rim from back right, soft metallic reflections, dark charcoal background gradient.
[6 MATERIALS & COLOR CODE] Block cast iron dark grey; head and piston aluminium light silver; rod and crank forged steel; section faces solid orange #FF7A1A; air particles light blue.
[7 CONTINUITY] Same engine design, section position, camera and lighting as K04 (attached).
[8 PHOTOREALISM] Photoreal 3D render, physically accurate, sharp focus.
[9 FORBIDDEN] {7.1}
```

**Örnek tam video promptu (S06, K05 → K06):**
```
[SHOT] S06 of 11, 5s, vertical 9:16, photoreal, continuous single take, no cuts.
[START] Begins exactly on the first frame: section view, piston at bottom dead center, intake valves open, cylinder full of light-blue air particles.
[END] Ends exactly on the last frame: piston at top dead center, all four valves closed, compressed air glowing orange in the small chamber above the piston.
[CAMERA] Starts 1.6 m from the section at piston height; slow dolly-in of 0.5 m while tilting up 10 degrees to frame the combustion chamber; smooth ease-in-out; no shake.
[MOTION in order] 0.0-0.6s: the two intake valves close upward smoothly. 0.6-4.4s: the piston rises steadily from bottom to top; the connecting rod swings from slightly right to vertical; the crankshaft rotates clockwise as seen from the camera, half a turn. The air particles are pushed into a smaller and smaller space and become denser. Their color shifts gradually from light blue to orange as they compress. 4.4-5.0s: the piston holds at the top; the orange glow intensifies slightly.
[KEEP CONSTANT] Same engine design, part count, orange section faces, lighting and background as both frames. No valve opens. Nothing appears or disappears.
[FORBIDDEN] {7.1}
```

---

## 9. Otomatik kalite kontrolü

**Anahtar kare seviyesi:** 7.6 promptu. Geçemeyen kare 3 kez yeniden üretilir.

**Sahne seviyesi** (her `S*.mp4`):
- 2 fps ile kare örneklenir ve 7.6 promptuyla denetlenir (insan/kadın, yazı/logo, morfing, parça tutarlılığı).
- İlk ve son kare, verilen anahtar karelerle karşılaştırılır (görsel benzerlik eşiği; örn. SSIM veya embedding benzerliği config'den).
- Süre, çözünürlük ve en-boy oranı kontrol edilir.

**Final video seviyesi:**
- Süre 30–55 sn; 1080×1920; 30 fps; ses -14 LUFS ±1.
- **Müzik kontrolü:** Ses izinin anlatıcı ve SFX dışında içerik barındırmadığı doğrulanır. Videonun kendi ses izi baştan atılır. Ek güvenlik için basit bir müzik/ton algılama (spektral sürekli tonal içerik) yapılır, şüphe durumunda bayrak konur.
- Altyazı senkronu: her kelimenin altyazı zamanı TTS zaman damgasıyla ±80 ms.
- Ekran yazılarında yazım kontrolü.
- **Kadın kontrolü** tüm final video boyunca 1 fps ile tekrar yapılır. Tek bir şüpheli kare bile videoyu `rejected_auto` yapar ve ilgili sahneyi yeniden üretime sokar.
- Rapor: `jobs/<id>/qc_report.json` + inceleme panelinde Türkçe özet.

---

## 10. İnceleme ve düzeltme sistemi (Ahmet'in paneli)

**Adres:** `http://localhost:8080` (yerel). Arayüz dili Türkçe.

### 10.1 Ana ekranlar
1. **Bekleyenler (awaiting_review):** Kart listesi: kapak karesi, başlık, süre, maliyet, otomatik kalite puanı, planlanan yayın tarihi.
2. **Video sayfası:**
   - Büyük dikey video oynatıcı. Klavye: boşluk = oynat/durdur, ←/→ = 1 kare.
   - **Sahne şeridi:** S01…S11 küçük resimleri. Tıklayınca o sahneye atlar. Her sahnenin altında kendi promptu ("prompt'u göster") ve anahtar kareleri görünür.
   - **Anlatım metni:** satır satır, doğrudan düzenlenebilir.
   - **Zaman damgalı not:** Videoyu durdurup "Bu ana not ekle" denince o anki saniye ve sahne otomatik eklenir. Ör. "0:23 — enjektör ortada değil, solda kalmış".
   - **Hızlı sorun etiketleri** (tek tıkla, sahneye bağlanır): `kadın/insan var`, `müzik/garip ses`, `parça yanlış/saçma`, `gerçekçi değil`, `yazı/logo var`, `geçiş sert`, `kamera kötü`, `anlatım hatalı`, `altyazı hatalı`, `ses efekti kötü`, `çok yavaş`, `çok hızlı`.
   - **Başlık/açıklama/etiketler:** düzenlenebilir alanlar.
   - Butonlar: **✅ Onayla**, **✏️ Düzeltme iste**, **❌ Reddet (konu çöpe)**, **🔁 Komple yeniden üret**.
3. **Takvim:** Önümüzdeki 14+ günün yayın slotları (günde 2), hangi videonun hangi slota atandığı. Sürükle-bırak ile sıra değiştirilebilir. Tampon göstergesi: "7 gün önde ✅" ya da "4 gün önde ⚠️".
4. **Yayına hazır:** Onaylanmış ve slotu gelen videolar, yükleme paketiyle birlikte (Bölüm 12). "Yükledim" butonu → `published`.
5. **Maliyet:** Günlük, haftalık ve aylık harcama; video başı ortalama; servis bazında kırılım; bütçe limiti göstergesi.

### 10.2 Düzeltme akışı
1. Ahmet notları ve etiketleri girer → **Düzeltme iste**.
2. Sistem 7.7 promptu ile notları yorumlar. Hangi kare, sahne, anlatım satırı, altyazı ya da efekt etkileniyor çıkarılır.
3. Belirsiz not varsa panelde **soru** olarak gösterilir. Ahmet cevaplamadan üretim başlamaz.
4. Ahmet'e **düzeltme planı** gösterilir: "K06 ve S06–S07 yeniden üretilecek, tahmini maliyet 4,20 $". Ahmet **Onayla** der.
5. Yalnızca etkilenen parçalar yeniden üretilir. Bir anahtar kare değişirse, o kareyi kullanan iki sahne de yeniden üretilir. Anlatım değişirse ses ve süreler yeniden hesaplanır.
6. Yeni sürüm `v2`, `v3`… olarak saklanır. Panelde **önceki sürümle yan yana** karşılaştırma yapılabilir. Hangi promptun neye değiştiği fark (diff) olarak gösterilir.
7. Aynı video için 3 düzeltme turundan sonra sistem uyarır: "Bu konu zorlanıyor; yeniden mi yazalım, çöpe mi atalım?"
8. Düzeltme notları `channels/k1/learnings.md` dosyasına özetlenerek eklenir. Ör. "Enjektör her zaman silindir ekseninin tam ortasında ve dikey olmalı". Bu öğrenimler sonraki tüm senaryo ve kare promptlarına **otomatik eklenir**. Sistem zamanla aynı hatayı tekrar etmez.

### 10.3 Bildirim
- Yeni video incelemeye düştüğünde, tampon 10 videonun altına indiğinde ya da bir iş `needs_attention` durumuna düştüğünde: masaüstü bildirimi. İsteğe bağlı: Telegram botu (config). Mesajlar Türkçe.

---

## 11. Takvim ve tampon (1 hafta önde)

- **Yayın:** Günde 2 video. Önerilen yayın saatleri ABD izleyicisi için ET 11:00 ve 18:00; Türkiye saatiyle ~18:00 ve ~01:00. Config'de değiştirilebilir. Ahmet YouTube Studio'nun zamanlama özelliğiyle önden planlayabilir.
- **Tampon hedefi:** Her an **en az 14 onaylı** video (7 günlük). Ek olarak inceleme ve üretimdekiler için 6 videoluk pay. Planlayıcı her gece (config: 02:00) şunu hesaplar:
  `üretilecek = max(0, 20 − (onaylı_planlanmamış + inceleme_bekleyen + üretimde))`
  ve o kadar job başlatır. Günlük üretim tavanı: `max_new_jobs_per_day` (varsayılan 4).
- **Başlangıç:** İlk yayından önce **14 video** üretilip onaylanmalı. Pilot sonrası "ilk parti" modu: günde 4–6 video üretimiyle ~3–4 gün.
- Onaylanan video otomatik olarak en yakın boş slota atanır. Ahmet takvimden değiştirebilir.
- Aynı cihaz kategorisi (ör. iki motor videosu) aynı gün üst üste konmaz.

---

## 12. Yükleme paketi (elle yükleme için)

Her onaylı video için `ready/<YYYY-MM-DD>_<slot>_<job_id>/` klasörü:
- `video.mp4`
- `title.txt`: İngilizce, en fazla 60 karakter, merak uyandıran ama yalan içermeyen başlık. Ör. "This SUV Has No Spark Plugs. So How Does It Run?"
- `description.txt`: 2–3 cümle açıklama + "Sources:" altında araştırma kaynakları + 3–5 hashtag (`#shorts #howitworks #engineering ...`).
- `tags.txt`
- `pinned_comment.txt`: Yorum çekecek bir soru.
- `thumbnail.png`
- `CHECKLIST.txt` (Türkçe): "YouTube'da 'Altered or synthetic content' kutusunu işaretle", "Yayın saati: …", "Kategori: Science & Technology", "Dil: İngilizce".

---

## 13. Maliyet ve bütçe koruması

**Tahmini video başı maliyet** (Ekim 2026 fal.ai fiyatları; kurulumda doğrula):

| Kalem | 720p | 480p + netlik artırma |
|---|---|---|
| Video (~46 sn + %30 yeniden deneme payı) | ~28 $ | ~13 $ |
| Anahtar kareler (~12 + yeniden denemeler, ~18 × 0,13 $) | ~2,4 $ | ~2,4 $ |
| Seslendirme + SFX | ~0,5 $ | ~0,5 $ |
| Claude (araştırma, senaryo, kalite kontrol) | ~1–2 $ | ~1–2 $ |
| **Toplam** | **~32 $** | **~17 $** |

Ayda ~60 video ile, her sahne AI video olursa: 720p ≈ **1.900 $**, 480p ≈ **1.000 $**. Ahmet'in hedefi ~1.000 $/ay ve altı. Bu yüzden:

**Varsayılan mod: HİBRİT (bütçe dostu).** Her sahne AI video olmak zorunda değil:
- **AI video (Seedance)** yalnızca gerçek hareketin şart olduğu sahnelerde kullanılır: araba sürüşü, piston hareketi, ateşleme, tekerin dönmesi. Video başı üst sınır `max_ai_video_seconds_per_video`, varsayılan **24 sn**.
- Kalan sahneler, onaylı **anahtar kareler** üzerinde sinematik kamera hareketiyle (yavaş yaklaşma, kaydırma, paralaks) ve iki kare arası yumuşak geçişle yapılır. Bu sahneler FFmpeg ile üretilir, maliyeti sıfırdır.
- Hibrit modda tahmini maliyet: video başı **~10–11 $**, ayda 60 video için **~650 $**.
- Pilot videoda (Aşama 6) aynı videonun hibrit ve tam AI sürümleri üretilir. Ahmet karşılaştırıp modu config'den seçer.

Ek önlemler:
- `video_resolution` config'de; **varsayılan "480p"** + 1080×1920'ye netlik artırarak ölçekleme. Pilot videoda Ahmet ikisini karşılaştırıp seçer.
- Alternatif sağlayıcıların (BytePlus doğrudan API, diğer aracı sağlayıcılar) Seedance 2.5 fiyatları kurulumda karşılaştırılır ve Ahmet'e tablo sunulur.
- **Koruma kuralları:** Video başı maliyet tavanı (`max_cost_per_video`, varsayılan 15 $), günlük tavan (`max_cost_per_day`), aylık tavan (`max_cost_per_month`). Tavana yaklaşınca yeni job başlamaz ve Ahmet'e bildirim gider.
- Pahalı adımdan (video) önce ucuz kontroller (anahtar kare kalite kontrolü) **zorunlu**dur.
- Her API çağrısının maliyeti loglanır.

---

## 14. Veri yapıları ve klasörler

```
shorts-system/
  CLAUDE.md                      # bu belge
  .env                           # API anahtarları (git'e girmez)
  config.yaml                    # genel ayarlar (bütçe, saatler, çözünürlük, eşikler)
  channels/
    k1/
      channel.yaml               # kanal kimliği, ses id, stil, renk kodu
      ideas.yaml                 # konu havuzu
      prompts/                   # 7.1–7.7 prompt dosyaları
      style_refs/                # onaylı altın standart kareler
      learnings.md               # düzeltmelerden öğrenilenler
      examples/diesel_engine.json# Bölüm 8 altın standart sahne listesi
  core/                          # kanal-bağımsız çekirdek
    pipeline/ (research.py, script.py, refs.py, keyframes.py, voice.py, shots.py, sfx.py, assemble.py, qc.py, revise.py, schedule.py, package.py)
    providers/ (fal_seedance.py, gemini_image.py, anthropic_llm.py, elevenlabs.py, image_search.py)
    db.py, costs.py, notify.py
  review_app/                    # FastAPI + statik HTML/JS
  assets/ (ref_library/, sfx_cache/, fonts/)
  jobs/<job_id>/ (facts.json, script.json, refs/, keyframes/, audio/, shots/, final/, qc_report.json, versions/, log.jsonl)
  ready/                         # yükleme paketleri
  tests/
```

**`script.json` şeması (özet):**
```json
{
  "job_id": "k1-0001", "title": "...", "total_duration_s": 46, "narration_full": "...",
  "shots": [{
    "id": "S05", "beat": 4, "duration_s": 4,
    "narration": "First, the piston slides down and pulls in air. Only air.",
    "start_keyframe": "K04", "end_keyframe": "K05",
    "start_frame_desc": "...", "end_frame_desc": "...",
    "camera_move": {"from": "...", "path": "...", "to": "...", "speed": "slow", "easing": "ease-in-out"},
    "motion": [{"t0": 0.0, "t1": 3.5, "what": "piston moves down from TDC to BDC"}],
    "effects": "...", "overlay_label": {"n": "STROKE 01 / 04", "t": "INTAKE"}, "hud": null,
    "sfx": [{"t": 0.2, "prompt": "air intake hiss inside engine, close-up"}],
    "refs_needed": ["cutaway_cylinder", "cylinder_head_valves"], "fact_ids": ["f3"]
  }],
  "title_yt": "...", "description_yt": "...", "tags": ["..."], "pinned_comment": "..."
}
```

**SQLite tabloları:** `jobs` (id, idea_id, status, version, created_at, cost_usd, qc_score, slot_date, slot_index), `assets` (job_id, kind, path, version, prompt_hash, seed, cost), `reviews` (job_id, version, decision, notes, tags, created_at), `costs` (ts, job_id, service, units, usd), `ideas`.

---

## 15. Kurulum aşamaları (Claude Code bunları sırayla uygular)

Her aşamanın sonunda: kabul testlerini çalıştır, sonucu Türkçe özetle göster, **Ahmet'in onayını al**, sonra devam et.

**Aşama 0 — Ortam ve anahtarlar**
- Python sanal ortamı ya da Docker Compose (Ahmet'e sor). FFmpeg kurulu mu kontrol et, değilse kurdur.
- `.env` şablonu oluştur, anahtarları Ahmet'ten iste. Her servise küçük bir "ping" çağrısı yap.
- **Kabul:** 5 servisin hepsi yanıt veriyor. FFmpeg sürümü yazdırılıyor.

**Aşama 1 — API doğrulama ve fiyat tablosu**
- Seedance 2.5 (image-to-video, end frame, 9:16, `generate_audio false`), Gemini 3 Pro Image (çoklu referans, 9:16), ElevenLabs TTS (zaman damgalı) ve SFX için güncel dokümanları oku. Küçük birer test çağrısı yap.
- Seedance için 2–3 sağlayıcının fiyatını karşılaştır.
- **Kabul:** 4 sn'lik test videosu (480p, 9:16, sessiz), 1 test görseli, 1 test sesi üretildi. Fiyat tablosu Ahmet'e sunuldu.

**Aşama 2 — Çekirdek + veritabanı + maliyet takibi**
- Klasör yapısı, `config.yaml`, SQLite, iş durum makinesi, log, maliyet kaydı, bütçe korumaları.
- **Kabul:** Sahte (mock) sağlayıcılarla bir job tüm durumlardan geçiyor. Maliyet tavanı testi job'u durduruyor.

**Aşama 3 — Araştırma + senaryo**
- Adım 2–3. Prompt dosyaları, JSON şema doğrulama, Bölüm 8 few-shot örneği.
- **Kabul:** "Diesel engine" ve "How a CPU works" için `facts.json` + `script.json` üretildi. Şema geçerli; 6 vuruş, tam zincir, kaynaklı iddialar ve yasak listesi mevcut. Ahmet metni okuyup onaylıyor.

**Aşama 4 — Referans görsel sistemi**
- Adım 4 / Bölüm 6. Wikimedia + Openverse + Pexels; lisans kaydı; görsel puanlama; kütüphane.
- **Kabul:** Dizel motor için kategori başına en az 3 kaliteli referans; `manifest.json` lisanslarıyla dolu. Ahmet referansları panelde görüyor.

**Aşama 5 — Anahtar kareler + kare kalite kontrolü**
- Adım 5. Sıralı üretim, stil referansı zinciri, 7.6 kontrolü, yeniden deneme.
- **Kabul:** Dizel motor için K00–K11 üretildi ve hepsi kontrolden geçti. Ahmet kareleri tek tek görüp onaylıyor. Gerekirse buradaki geri bildirimler prompt şablonlarına işleniyor. **Bu aşama kalite için en kritik aşamadır; acele etme.**

**Aşama 6 — Pilot video (uçtan uca)**
- Adım 6–10: ses, sahneler (önce **480p**), SFX, montaj, otomatik kalite kontrolü.
- Aynı videonun 1–2 sahnesini 720p'de de üret. Ahmet kaliteyi karşılaştırıp çözünürlüğe karar versin.
- **Kabul:** 40–50 sn'lik dizel motor videosu; kadın yok, müzik yok, yazı/logo yok; kesintisiz geçişler; tam zincir (araba yolda gidiyor). Ahmet izleyip onaylıyor. Onaylanan en iyi kareler `style_refs/` klasörüne kopyalanıyor.

**Aşama 7 — İnceleme paneli + düzeltme sistemi**
- Bölüm 10'un tamamı.
- **Kabul:** Ahmet pilot videoya zaman damgalı bir not yazıyor. Sistem doğru sahneyi buluyor, plan ve maliyet gösteriyor, yalnızca o sahneyi yeniden üretiyor, v1 ve v2 yan yana izlenebiliyor, öğrenim `learnings.md` dosyasına ekleniyor.

**Aşama 8 — Takvim, tampon, yükleme paketi, bildirim**
- Bölüm 11–12, 10.3.
- **Kabul:** Takvim 14 günü gösteriyor, tampon formülü çalışıyor, `ready/` paketleri eksiksiz, bildirim geliyor.

**Aşama 9 — İlk parti**
- 14 videoluk ilk parti (Bölüm 16'dan, farklı kategorilerden). Her video panelde incelenir.
- **Kabul:** 14 onaylı video ve 7 günlük tampon hazır. Gerçek video başı maliyet raporu Ahmet'e sunuldu.

**Aşama 10 — Sürekli çalışma**
- Gece planlayıcısı, otomatik başlatma (Windows Görev Zamanlayıcı ya da Docker restart policy), günlük sağlık raporu.
- Kanal 2 ve 3 için gereken genişletme noktaları (`channels/<kanal>/`) belgelenir.

---

## 16. Kanal 1 video fikirleri (başlangıç havuzu)

Her fikirde tam zincir zorunludur: **dış sahne → içeri dalış → mekanizma → "sonra ne oluyor?" → gerçek dünyadaki sonuç.** Tüm cihazlar markasız, sahnelerde insan yok.

| # | Konu | Dış sahne (açılış) | Mekanizma | Tam zincir → sonuç |
|---|---|---|---|---|
| 1 | Dizel motor | SUV yolda gidiyor | 4 zaman, sıkıştırma ile ateşleme | krank → şanzıman → kardan → teker → araba gider |
| 2 | Benzinli motor | Sedan şehirde | 4 zaman, buji kıvılcımı | krank → şanzıman → teker |
| 3 | İşlemci (CPU) | Masada açık bilgisayar, ekranda oyun | Transistör açılıp kapanır, saat sinyali, komut hattı | elektrik → mantık kapıları → hesap → görüntü kartı → ekranda kare |
| 4 | Split klima | Sıcak oda, duvarda klima | Kompresör, kondenser, genleşme valfi, evaporatör | soğutucu ısıyı dışarı taşır → içeriye soğuk hava → oda serinler |
| 5 | Televizyon (OLED) | Karanlık odada açık TV | Piksel başına organik LED, kırmızı-yeşil-mavi alt pikseller | sinyal → piksel akımı → ışık → görüntü |
| 6 | LCD televizyon | Salon TV'si | Arka ışık, polarizör, sıvı kristal kapakçık | ışık → kristal döner → renk filtresi → görüntü |
| 7 | Buzdolabı | Mutfakta buzdolabı | Kompresör, kılcal boru, evaporatör | ısı içeriden çekilir → arkadan atılır → içerisi soğur |
| 8 | Otomatik şanzıman | Araba kalkış yapıyor | Tork konvertörü, planet dişliler | motor → tork konvertörü → planet dişli → teker |
| 9 | Debriyaj (manuel) | Araç vites değiştiriyor | Baskı plakası, disk, volan | motor ↔ şanzıman bağlanır → araç hareket eder |
| 10 | Disk fren + ABS | Araba yağmurda fren yapıyor | Hidrolik, kaliper, ABS valfi | pedal → hidrolik basınç → balata → disk → araç durur |
| 11 | Turboşarj | Kamyon yokuş çıkıyor | Egzoz türbini, kompresör | egzoz → türbin → kompresör → daha çok hava → daha çok güç |
| 12 | Elektrikli araba motoru | Elektrikli araba sessizce kalkıyor | Batarya, invertör, döner manyetik alan | batarya → invertör → stator → rotor → teker |
| 13 | Lityum iyon batarya | Telefon şarjda | Lityum iyonlarının anot ve katot arası hareketi | şarj → iyon depolama → deşarj → telefon çalışır |
| 14 | Jet motoru | Yolcu uçağı kalkışta | Fan, kompresör, yanma odası, türbin | itki → uçak kalkar |
| 15 | Helikopter rotoru | Helikopter havalanıyor | Swashplate, kolektif ve döngüsel hatve | pervane açısı → kaldırma → yön |
| 16 | Asansör | Gökdelen asansörü | Çekiş kasnağı, karşı ağırlık, emniyet freni | motor → halat → kabin yükselir |
| 17 | Yürüyen merdiven | Alışveriş merkezi | Zincir, basamak rayları | motor → zincir → basamaklar düzleşir/yükselir |
| 18 | Çamaşır makinesi | Banyoda çalışan makine | Tambur, motor, pompa, sıkma | su + dönüş → kir çözülür → sıkma ile su atılır |
| 19 | Bulaşık makinesi | Mutfakta | Pompa, dönen kollar, ısıtıcı | sıcak su jetleri → temiz tabaklar |
| 20 | Mikrodalga fırın | Mikrodalga çalışıyor | Magnetron, dalga kılavuzu | mikrodalga → su molekülleri titreşir → yemek ısınır |
| 21 | İndüksiyon ocak | Tencere kaynıyor | Bobin, girdap akımları | manyetik alan → tencerede akım → ısı |
| 22 | Elektrik süpürgesi (siklon) | Halıda süpürge | Motor, fan, siklon ayırma | vakum → hava döner → toz ayrılır |
| 23 | Rüzgâr türbini | Tepede türbin | Kanatlar, şanzıman, jeneratör | rüzgâr → dönüş → elektrik → şehir ışıkları |
| 24 | Hidroelektrik santrali | Baraj | Cebri boru, türbin, jeneratör | düşen su → türbin → elektrik |
| 25 | Nükleer santral | Soğutma kuleleri | Fisyon, buhar jeneratörü, türbin | ısı → buhar → türbin → elektrik |
| 26 | Güneş paneli | Çatıda panel | Fotovoltaik hücre, elektron akışı | güneş ışığı → akım → invertör → ev |
| 27 | Hidrolik ekskavatör | Şantiyede kazı | Pompa, silindirler, valfler | motor → hidrolik basınç → kol hareket eder |
| 28 | Dizel-elektrik lokomotif | Yük treni | Dizel motor → jeneratör → çekiş motorları | elektrik → tekerler → tren ilerler |
| 29 | Mekanik kol saati | Bilekte saat (erkek bileği, yüz yok) | Zemberek, eşapman, balans çarkı | enerji adım adım → akrep ve yelkovan |
| 30 | Telefon kamerası | Telefon fotoğraf çekiyor | Lens, otomatik odak motoru, sensör | ışık → piksel → işlemci → fotoğraf |
| 31 | SSD | Bilgisayar açılıyor | Flash hücre, yüzen kapı | yük depolanır → veri okunur → sistem açılır |
| 32 | Hava yastığı | Çarpışma testi mankeni (cinsiyetsiz, insan değil) | Sensör, gaz üreteci | çarpma → ~30 ms'de şişme |
| 33 | 3D yazıcı | Masada parça basıyor | Ekstrüder, step motorlar | eriyik plastik katman katman → nesne |
| 34 | Gemi pervanesi ve dümen | Kargo gemisi | Dizel motor, şaft, pervane | itki → gemi ilerler |
| 35 | Klozet sifonu | Banyo | Sifon etkisi, şamandıra | su akışı → sifon → tank dolar |
| 36 | Fren yapan tren (rejeneratif) | Metro istasyona giriyor | Motor jeneratör olur | hareket → elektrik → şebekeye geri |

---

## 17. Bilinen riskler ve önlemler

| Risk | Önlem |
|---|---|
| Video modeli ilk ve son kare arasında parçaları değiştiriyor (morfing) | Sahneleri kısa tut (3–6 sn). Promptta "nothing appears or disappears" kuralı. Sahne kalite kontrolü ve yeniden deneme. Gerekirse sahneyi iki kısa sahneye böl. |
| Ardışık sahnelerde motor tasarımı kayıyor | Ortak anahtar kare + stil referansı zinciri + kanal `style_refs`. |
| Model istemeden ses ya da müzik üretiyor | `generate_audio: false` + video ses izi her zaman atılır. |
| İnsan ya da kadın beliriyor (ör. araba sahnesinde sürücü) | Koyu cam, "no people" kuralı, 1 fps kontrol, otomatik ret. |
| Yazı, logo ya da plaka beliriyor | Yasak listesi + kalite kontrolü + gerekirse kırp/bulanıklaştır yerine yeniden üret. |
| Yanlış teknik bilgi | İki kaynaklı doğrulama, `fact_ids` zorunluluğu, Ahmet incelemesi. |
| Maliyet kontrolden çıkıyor | Tavanlar, önce ucuz kontrol, maliyet paneli, 480p varsayılan. |
| YouTube "inauthentic content" politikası | Her video özgün araştırma ve anlatım; aynı konuyu kopyalama; şablon değil format. |
| API değişiklikleri | Sağlayıcılar `providers/` altında ayrı modüller; endpoint ve parametreler config'de. |
| Bilgisayar kapanırsa | Idempotent adımlar, kaldığı yerden devam, açılışta otomatik başlatma. |

---

## 18. Son hatırlatma (Claude Code için)

1. Videolarda **kadın yok**, varsayılan olarak **hiç insan yok**.
2. **Müzik yok.**
3. Format **YouTube Shorts**: 9:16, 1080×1920, 30–55 sn.
4. Promptlar **aşırı ayrıntılı**: 9 başlıklı şablonlar eksiksiz.
5. **Günde 2 video, en az 1 hafta (14 video) önden**; ayrıntılı inceleme ve düzeltme sistemi.
6. **Her zaman referans görseller**: gerçek referanslar → anahtar kareler → video. Uydurma makine yok.
7. **Otomasyon + Ahmet'in kontrolü**; YouTube'a otomatik yükleme **yok**, yükleme paketi hazırlanır.
8. **Tam zincir**: "sonra ne oluyor?" sorusu, gerçek dünyadaki sonuca kadar sorulur (motor → teker → araba gider).
9. İlk konu yalnızca bir **örnektir**. Konu havuzu Bölüm 16'dadır ve büyütülebilir.
10. Şüphede kalırsan **Ahmet'e sor**.
