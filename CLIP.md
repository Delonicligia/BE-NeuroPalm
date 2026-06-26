# CLIP Image Filter Skill

## Tujuan
Skill ini memandu agent AI untuk mengimplementasikan CLIP (Contrastive Language–Image Pre-training) dari OpenAI sebagai **filter/gatekeeper** pada backend FastAPI sebelum gambar masuk ke model klasifikasi utama.

---

## Kapan Menggunakan Skill Ini
- Ketika endpoint FastAPI menerima upload gambar dari pengguna
- Ketika hanya gambar dari kategori spesifik yang boleh diproses model utama
- Ketika perlu menolak gambar tidak relevan dengan pesan yang informatif
- Ketika ingin validasi konten gambar tanpa fine-tuning model tambahan

---

## Dependencies yang Diperlukan

```bash
pip install torch torchvision
pip install git+https://github.com/openai/CLIP.git
pip install fastapi python-multipart pillow numpy
```

> **Catatan:** CLIP berjalan di CPU maupun GPU. Di production, gunakan GPU untuk performa lebih baik.

---

## Arsitektur Pipeline

```
Request Upload Gambar
        │
        ▼
  [FastAPI Endpoint]
        │
        ▼
  [CLIP Filter]  ──── skor < threshold ──▶  Tolak (400 Bad Request)
        │
   skor ≥ threshold
        │
        ▼
  [Model Klasifikasi Utama]
        │
        ▼
     Response
```

---

## Implementasi

### 1. Struktur File

```
project/
├── main.py
├── clip_filter.py        ← modul CLIP filter
├── classifier.py         ← model klasifikasi kamu
├── requirements.txt
└── CLIP.md               ← file ini
```

---

### 2. Modul CLIP Filter (`clip_filter.py`)

```python
import clip
import torch
from PIL import Image
import io
from functools import lru_cache
from typing import Tuple


@lru_cache(maxsize=1)
def load_clip_model() -> Tuple:
    """
    Load model CLIP sekali saat startup, cache untuk reuse.
    Gunakan ViT-B/32 untuk keseimbangan kecepatan dan akurasi.
    Opsi lain: ViT-L/14 (lebih akurat, lebih lambat)
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()
    return model, preprocess, device


class CLIPFilter:
    """
    Filter gambar menggunakan CLIP zero-shot classification.
    
    Parameters:
        positive_prompts: daftar deskripsi gambar yang DITERIMA
        negative_prompts: daftar deskripsi gambar yang DITOLAK
        threshold: nilai minimum similarity agar gambar lolos (0.0 - 1.0)
    """

    def __init__(
        self,
        positive_prompts: list[str],
        negative_prompts: list[str],
        threshold: float = 0.6
    ):
        self.positive_prompts = positive_prompts
        self.negative_prompts = negative_prompts
        self.threshold = threshold
        self.model, self.preprocess, self.device = load_clip_model()

        # Tokenize semua prompt sekali, cache hasilnya
        all_prompts = positive_prompts + negative_prompts
        self.text_tokens = clip.tokenize(all_prompts).to(self.device)

        with torch.no_grad():
            self.text_features = self.model.encode_text(self.text_tokens)
            self.text_features /= self.text_features.norm(dim=-1, keepdim=True)

    def is_valid(self, image_bytes: bytes) -> Tuple[bool, float, str]:
        """
        Periksa apakah gambar sesuai dengan kategori yang diizinkan.

        Returns:
            (is_valid, confidence_score, message)
        """
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return False, 0.0, "File bukan gambar yang valid"

        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            image_features = self.model.encode_image(image_tensor)
            image_features /= image_features.norm(dim=-1, keepdim=True)

            # Hitung similarity dengan semua prompt
            similarities = (image_features @ self.text_features.T).squeeze(0)
            probs = similarities.softmax(dim=0).cpu().numpy()

        # Jumlahkan probabilitas untuk positive prompts
        n_positive = len(self.positive_prompts)
        positive_score = float(probs[:n_positive].sum())

        is_valid = positive_score >= self.threshold
        message = (
            "Gambar valid, melanjutkan ke analisis"
            if is_valid
            else f"Gambar tidak sesuai (skor: {positive_score:.2f}). "
                 f"Harap upload gambar yang tepat."
        )

        return is_valid, positive_score, message
```

---

### 3. Integrasi ke FastAPI (`main.py`)

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from clip_filter import CLIPFilter
from classifier import predict  # model klasifikasi kamu

app = FastAPI(title="API Klasifikasi Biji Pinang")

# ── Inisialisasi CLIP Filter ──────────────────────────────────────────────────
# Sesuaikan prompt dengan kebutuhan proyekmu
clip_filter = CLIPFilter(
    positive_prompts=[
        "a photo of areca nut",
        "a photo of betel nut",
        "a close-up photo of pinang fruit",
        "a photo of areca palm fruit",
    ],
    negative_prompts=[
        "a photo of something else",
        "a photo of a person",
        "a photo of an animal",
        "a photo of a landscape",
        "a photo of food that is not areca nut",
    ],
    threshold=0.55  # tuning sesuai kebutuhan: lebih tinggi = lebih ketat
)


# ── Endpoint Prediksi ─────────────────────────────────────────────────────────
@app.post("/predict")
async def predict_quality(file: UploadFile = File(...)):
    """
    Endpoint untuk prediksi kualitas biji pinang.
    
    - CLIP memvalidasi gambar terlebih dahulu
    - Jika lolos, model klasifikasi memberikan prediksi kelas
    """
    # Validasi tipe file
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File harus berupa gambar (jpg, png, dll)"
        )

    image_bytes = await file.read()

    # ── Tahap 1: CLIP Filter ──
    is_valid, confidence, message = clip_filter.is_valid(image_bytes)

    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Gambar tidak valid",
                "message": message,
                "clip_score": round(confidence, 4),
                "hint": "Pastikan gambar menampilkan biji pinang dengan jelas"
            }
        )

    # ── Tahap 2: Klasifikasi ──
    prediction = predict(image_bytes)  # fungsi dari classifier.py kamu

    return JSONResponse({
        "status": "success",
        "clip_score": round(confidence, 4),
        "prediction": prediction["class"],       # contoh: "Kelas A"
        "confidence": prediction["confidence"],  # contoh: 0.92
    })


# ── Endpoint Health Check ─────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "model": "ViT-B/32", "threshold": clip_filter.threshold}
```

---

## Konfigurasi Threshold

Threshold mengontrol seberapa ketat filter bekerja:

| Nilai | Perilaku | Cocok Untuk |
|-------|----------|-------------|
| `0.45–0.55` | Longgar — banyak gambar lolos | Tahap development / testing |
| `0.55–0.65` | Sedang — keseimbangan baik | **Rekomendasi production** |
| `0.65–0.80` | Ketat — hanya gambar jelas | Ketika FP harus sangat rendah |

> **Tips tuning:** Kumpulkan 20–30 gambar valid dan 20–30 gambar tidak valid, jalankan melalui filter, cek distribusi skor, pilih threshold di antara dua kelompok.

---

## Prompt Engineering untuk CLIP

Kualitas prompt sangat mempengaruhi hasil. Gunakan pola berikut:

```python
# ✅ Prompt yang baik — spesifik dan deskriptif
positive_prompts = [
    "a close-up photo of areca nut",
    "a photo of betel nut fruit",
    "areca palm seeds on a surface",
]

# ❌ Prompt yang buruk — terlalu umum
positive_prompts = [
    "pinang",        # terlalu pendek
    "fruit",         # terlalu luas
    "good image",    # tidak deskriptif
]
```

### Template prompt yang terbukti efektif:
```
"a photo of [objek]"
"a close-up photo of [objek]"
"a [adjective] photo of [objek] on [background]"
"[objek] viewed from [angle]"
```

---

## Penanganan Error

| Kode | Kondisi | Pesan |
|------|---------|-------|
| `400` | File bukan gambar | "File harus berupa gambar" |
| `422` | Gambar tidak lolos CLIP | "Gambar tidak valid" + skor |
| `500` | Error internal server | Log ke server, return generic error |

---

## Optimasi Performa

### Cache model (sudah diimplementasi)
```python
# load_clip_model() menggunakan @lru_cache
# Model hanya di-load SEKALI saat startup FastAPI
```

### Gunakan lifespan event untuk warmup
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warmup: load model saat startup
    load_clip_model()
    print("✅ CLIP model loaded")
    yield
    print("🛑 Shutdown")

app = FastAPI(lifespan=lifespan)
```

### Batch processing (opsional)
```python
# Jika perlu memproses banyak gambar sekaligus
async def predict_batch(files: list[UploadFile]):
    results = []
    for file in files:
        bytes_data = await file.read()
        valid, score, msg = clip_filter.is_valid(bytes_data)
        results.append({"valid": valid, "score": score})
    return results
```

---

## Contoh Response API

### Gambar valid (lolos filter)
```json
{
  "status": "success",
  "clip_score": 0.7823,
  "prediction": "Kelas A",
  "confidence": 0.9142
}
```

### Gambar ditolak CLIP
```json
{
  "detail": {
    "error": "Gambar tidak valid",
    "message": "Gambar tidak sesuai (skor: 0.23). Harap upload gambar yang tepat.",
    "clip_score": 0.2341,
    "hint": "Pastikan gambar menampilkan biji pinang dengan jelas"
  }
}
```

---

## Checklist Implementasi

- [ ] Install semua dependencies
- [ ] Buat `clip_filter.py` dengan `CLIPFilter` class
- [ ] Sesuaikan `positive_prompts` dan `negative_prompts` untuk biji pinang
- [ ] Integrasikan ke endpoint FastAPI yang ada
- [ ] Tuning `threshold` dengan data gambar nyata
- [ ] Tambahkan lifespan warmup agar startup lebih cepat
- [ ] Test dengan gambar valid dan tidak valid
- [ ] Monitor `clip_score` di log untuk evaluasi berkelanjutan

---

## Catatan untuk Agent AI

- Selalu panggil `load_clip_model()` dengan `@lru_cache` — jangan load ulang setiap request
- Text features boleh di-precompute saat init `CLIPFilter`, bukan saat setiap inferensi
- `image_bytes` lebih aman dikirim antar fungsi daripada path file (menghindari race condition)
- Jika threshold perlu dinamis, simpan di environment variable atau config file, bukan hardcode
- CLIP `ViT-B/32` adalah pilihan default yang baik; gunakan `ViT-L/14` hanya jika akurasi sangat kritis dan latensi bukan prioritas utama
