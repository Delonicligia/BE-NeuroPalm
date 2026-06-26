import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, base
from app.api.V1.endpoints import user_route, sawit_route, harga_route, riwayat_route 
from app.core.config import settings
from app.models import user_model, sawit_model, harga_model, riwayat_model  # noqa: F401 - import agar create_all membuat tabel

# Path absolut ke root project
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# Buat direktori uploads saat modul dimuat
os.makedirs(os.path.join(UPLOAD_DIR, "sawit"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)
    print("Database Connected")
    yield
    await engine.dispose()
    print("Database Disconnected")
    
app = FastAPI(lifespan=lifespan)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files untuk akses gambar via URL
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(user_route.router, prefix="/api") 
app.include_router(sawit_route.router, prefix="/api") 
app.include_router(harga_route.router, prefix="/api") 
app.include_router(riwayat_route.router, prefix="/api") 


@app.get("/")
def read_root():
    return {"Hello": "World"}