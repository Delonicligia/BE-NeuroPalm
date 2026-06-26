# Production Readiness Guide — FastAPI + CLIP

Panduan ini mencakup semua yang perlu disiapkan sebelum backend FastAPI + CLIP
kamu dapat melayani pengguna nyata di lingkungan production.

---

## Daftar Isi

1. [Struktur Project](#1-struktur-project)
2. [Environment & Konfigurasi](#2-environment--konfigurasi)
3. [Server & Performa](#3-server--performa)
4. [Keamanan (Security)](#4-keamanan-security)
5. [Validasi & Error Handling](#5-validasi--error-handling)
6. [Logging & Monitoring](#6-logging--monitoring)
7. [Model Management](#7-model-management)
8. [Containerisasi (Docker)](#8-containerisasi-docker)
9. [CI/CD Pipeline](#9-cicd-pipeline)
10. [Checklist Akhir](#10-checklist-akhir)

---

## 1. Struktur Project

Struktur yang disarankan untuk production:

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py               ← entry point FastAPI
│   ├── config.py             ← semua konfigurasi dari env
│   ├── dependencies.py       ← shared dependencies (model, db)
│   ├── routers/
│   │   ├── predict.py        ← endpoint prediksi
│   │   └── health.py         ← endpoint health check
│   ├── services/
│   │   ├── clip_filter.py    ← logika CLIP
│   │   └── classifier.py     ← logika model klasifikasi
│   └── schemas/
│       └── response.py       ← Pydantic response models
├── tests/
│   ├── test_predict.py
│   └── test_clip_filter.py
├── .env                      ← variabel environment (JANGAN di-commit)
├── .env.example              ← template env (boleh di-commit)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── requirements-dev.txt
```

---

## 2. Environment & Konfigurasi

### Jangan pernah hardcode nilai konfigurasi di kode.

Buat file `.env`:

```env
# App
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
APP_WORKERS=4

# CLIP
CLIP_MODEL=ViT-B/32
CLIP_THRESHOLD=0.55

# Security
API_KEY=ganti_dengan_key_yang_kuat
ALLOWED_ORIGINS=https://domainmu.com,https://www.domainmu.com
MAX_FILE_SIZE_MB=5

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

Buat `app/config.py` menggunakan Pydantic Settings:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_workers: int = 2

    # CLIP
    clip_model: str = "ViT-B/32"
    clip_threshold: float = 0.55

    # Security
    api_key: str = ""
    allowed_origins: list[str] = ["*"]
    max_file_size_mb: int = 5

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

---

## 3. Server & Performa

### Gunakan Uvicorn + Gunicorn (bukan `uvicorn main:app` langsung)

`uvicorn` saja hanya single-process. Di production, gunakan Gunicorn sebagai process manager:

```bash
pip install gunicorn
```

Jalankan dengan:

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5 \
  --log-level info \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

> **Rumus workers:** `(2 × jumlah_CPU) + 1`
> Contoh: 2 CPU → 5 workers

### Nonaktifkan reload & debug di production

```python
# main.py
import uvicorn
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,       # ← WAJIB False di production
        workers=settings.app_workers,
    )
```

### Nonaktifkan docs di production (opsional tapi disarankan)

```python
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="API Klasifikasi Biji Pinang",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    openapi_url="/openapi.json" if settings.app_env != "production" else None,
)
```

---

## 4. Keamanan (Security)

### 4.1 API Key Authentication

```python
# app/dependencies.py
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    settings = get_settings()
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key tidak valid atau tidak diberikan"
        )
    return api_key
```

Gunakan di endpoint:

```python
@app.post("/predict", dependencies=[Depends(verify_api_key)])
async def predict_quality(file: UploadFile = File(...)):
    ...
```

### 4.2 CORS — Batasi Origin

```python
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # bukan ["*"] di production!
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)
```

### 4.3 Rate Limiting

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/predict")
@limiter.limit("10/minute")   # maks 10 request per menit per IP
async def predict_quality(request: Request, file: UploadFile = File(...)):
    ...
```

### 4.4 Validasi File yang Ketat

```python
import imghdr
from app.config import get_settings

ALLOWED_TYPES = {"jpeg", "png", "webp"}
settings = get_settings()

async def validate_image(file: UploadFile) -> bytes:
    # Cek ukuran file
    image_bytes = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Ukuran file melebihi batas {settings.max_file_size_mb}MB"
        )

    # Cek tipe file dari konten (bukan hanya ekstensi)
    detected_type = imghdr.what(None, h=image_bytes)
    if detected_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipe file tidak didukung. Gunakan: {', '.join(ALLOWED_TYPES)}"
        )

    return image_bytes
```

### 4.5 Gunakan HTTPS

Selalu jalankan di belakang reverse proxy (Nginx/Caddy) dengan SSL/TLS.
Jangan pernah expose port FastAPI langsung ke internet.

```
Internet → Nginx (HTTPS :443) → FastAPI (HTTP :8000, lokal saja)
```

---

## 5. Validasi & Error Handling

### Response schema yang konsisten

```python
# app/schemas/response.py
from pydantic import BaseModel
from typing import Optional


class PredictionResponse(BaseModel):
    status: str
    clip_score: float
    prediction: str
    confidence: float


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[str] = None
```

### Global exception handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log detail error di server, jangan kirim ke client
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "Terjadi kesalahan pada server"}
    )
```

---

## 6. Logging & Monitoring

### Setup logging terstruktur

```python
# app/logger.py
import logging
import sys
from app.config import get_settings

settings = get_settings()


def setup_logger():
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    handlers = [logging.StreamHandler(sys.stdout)]

    if settings.log_file:
        import os
        os.makedirs("logs", exist_ok=True)
        handlers.append(logging.FileHandler(settings.log_file))

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=log_format,
        handlers=handlers
    )
```

### Log setiap request prediksi

```python
import logging
import time

logger = logging.getLogger(__name__)

@app.post("/predict")
async def predict_quality(file: UploadFile = File(...)):
    start = time.time()

    # ... proses prediksi ...

    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        f"predict | file={file.filename} | clip_score={clip_score:.4f} "
        f"| result={prediction} | duration={duration_ms}ms"
    )
```

### Health check endpoint yang informatif

```python
import torch
from datetime import datetime

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.app_env,
        "clip_model": settings.clip_model,
        "clip_threshold": settings.clip_threshold,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
    }
```

---

## 7. Model Management

### Preload model saat startup, bukan saat request

```python
from contextlib import asynccontextmanager
from app.services.clip_filter import CLIPFilter
from app.services.classifier import load_classifier

clip_filter_instance = None
classifier_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global clip_filter_instance, classifier_instance

    print("🚀 Memuat model...")
    clip_filter_instance = CLIPFilter(
        positive_prompts=[...],
        negative_prompts=[...],
        threshold=settings.clip_threshold
    )
    classifier_instance = load_classifier()
    print("✅ Semua model siap")

    yield  # ← aplikasi berjalan di sini

    print("🛑 Shutdown — membersihkan resource")
    # cleanup jika diperlukan

app = FastAPI(lifespan=lifespan)
```

### Simpan model lokal (jangan download saat startup production)

```bash
# Download sekali saat build/setup
python -c "import clip; clip.load('ViT-B/32')"
```

Model CLIP akan tersimpan di `~/.cache/clip/`. Pastikan direktori ini tersedia di container/server production.

---

## 8. Containerisasi (Docker)

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install sistem dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download dan cache model CLIP saat build (bukan saat runtime)
RUN python -c "import clip; clip.load('ViT-B/32')"

# Copy source code
COPY app/ ./app/

# Buat direktori logs
RUN mkdir -p logs

# Jalankan sebagai non-root user (keamanan)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120"]
```

### `docker-compose.yml`

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - api
    restart: unless-stopped
```

### `requirements.txt`

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
gunicorn>=21.0.0
python-multipart>=0.0.6
pillow>=10.0.0
torch>=2.0.0
torchvision>=0.15.0
git+https://github.com/openai/CLIP.git
pydantic>=2.0.0
pydantic-settings>=2.0.0
slowapi>=0.1.9
python-dotenv>=1.0.0
```

---

## 9. CI/CD Pipeline

### `.github/workflows/deploy.yml` (GitHub Actions)

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run tests
        run: pytest tests/ -v --tb=short

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy ke server
        uses: appleboy/ssh-action@v0.1.10
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/app
            git pull origin main
            docker compose build
            docker compose up -d --no-deps api
            docker compose ps
```

---

## 10. Checklist Akhir

Centang semua sebelum go-live:

### Konfigurasi
- [ ] Semua nilai sensitif ada di `.env`, tidak ada yang hardcode
- [ ] `.env` masuk `.gitignore`
- [ ] `.env.example` tersedia untuk referensi tim
- [ ] `APP_ENV=production` di server

### Server
- [ ] Menggunakan Gunicorn + UvicornWorker (bukan `uvicorn` langsung)
- [ ] `reload=False` dan `debug=False`
- [ ] Jumlah workers sesuai kapasitas CPU server
- [ ] Docs endpoint (`/docs`, `/redoc`) dinonaktifkan

### Keamanan
- [ ] API Key authentication aktif
- [ ] CORS dikonfigurasi hanya untuk domain yang diizinkan
- [ ] Rate limiting terpasang
- [ ] Validasi file: ukuran, tipe, dan konten
- [ ] Berjalan di belakang Nginx dengan HTTPS
- [ ] Container berjalan sebagai non-root user

### Model
- [ ] CLIP dan model klasifikasi di-preload saat startup
- [ ] Model CLIP sudah di-cache lokal (tidak download saat startup)
- [ ] Threshold CLIP sudah dituning dengan data nyata

### Logging & Monitoring
- [ ] Logging terstruktur aktif (INFO level minimum)
- [ ] Setiap request prediksi ter-log beserta durasi dan skor
- [ ] `/health` endpoint berfungsi dan mengembalikan info yang cukup
- [ ] Log disimpan ke file dan/atau monitoring tool

### Infrastruktur
- [ ] Docker image berhasil di-build tanpa error
- [ ] `docker-compose up` berjalan dan health check hijau
- [ ] Nginx reverse proxy terkonfigurasi dengan benar
- [ ] SSL certificate terpasang dan auto-renew (misalnya dengan Certbot)
- [ ] CI/CD pipeline berjalan dan test lulus sebelum deploy

### Testing
- [ ] Unit test untuk `CLIPFilter` dengan gambar valid dan tidak valid
- [ ] Integration test untuk endpoint `/predict`
- [ ] Load test untuk memastikan server stabil di bawah traffic

---

> **Catatan:** Dokumen ini adalah panduan hidup — perbarui setiap kali ada perubahan arsitektur atau kebutuhan baru di project.
