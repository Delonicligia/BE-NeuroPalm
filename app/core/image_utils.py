import os
import uuid
from datetime import datetime
from PIL import Image
from fastapi import UploadFile, HTTPException, status
import aiofiles

# Direktori penyimpanan gambar
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "sawit")

# Format gambar yang diizinkan
ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/jpg", "image/webp"}

# Maksimal ukuran file (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

# Ukuran resize gambar (opsional, untuk menghemat penyimpanan)
RESIZE_WIDTH = 800
RESIZE_HEIGHT = 800


def ensure_upload_dir():
    """Pastikan direktori upload ada"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def generate_filename(original_filename: str) -> str:
    """Generate nama file unik menggunakan UUID + timestamp"""
    ext = os.path.splitext(original_filename)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"sawit_{timestamp}_{unique_id}{ext}"


async def validate_image(file: UploadFile):
    """Validasi file: tipe dan ukuran"""
    # Cek content type
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format file tidak didukung. Gunakan: JPEG, PNG, atau WebP"
        )
    
    # Cek ukuran file
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ukuran file terlalu besar. Maksimal {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # Reset posisi file setelah dibaca
    await file.seek(0)
    return content


async def save_image(file: UploadFile, resize: bool = True) -> str:
    """
    Simpan gambar yang diupload menggunakan Pillow.
    
    Args:
        file: File yang diupload dari request
        resize: Apakah gambar perlu di-resize (default: True)
    
    Returns:
        Path relatif gambar yang disimpan (untuk disimpan di database)
    """
    # Validasi file
    content = await validate_image(file)
    
    # Pastikan direktori ada
    ensure_upload_dir()
    
    # Generate nama file unik
    filename = generate_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Simpan file sementara
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Proses gambar dengan Pillow
    try:
        with Image.open(filepath) as img:
            # Convert ke RGB jika RGBA (PNG dengan transparansi)
            if img.mode == "RGBA":
                img = img.convert("RGB")
            
            # Resize jika diminta
            if resize:
                img.thumbnail((RESIZE_WIDTH, RESIZE_HEIGHT), Image.LANCZOS)
            
            # Simpan dengan optimasi
            save_kwargs = {"optimize": True}
            if filepath.lower().endswith((".jpg", ".jpeg")):
                save_kwargs["quality"] = 85
            elif filepath.lower().endswith(".webp"):
                save_kwargs["quality"] = 85
            
            img.save(filepath, **save_kwargs)
    except Exception as e:
        # Hapus file jika gagal diproses
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gagal memproses gambar: {str(e)}"
        )
    
    # Return path relatif untuk disimpan di database
    return f"uploads/sawit/{filename}"


def delete_image(image_path: str) -> bool:
    """
    Hapus file gambar dari storage.
    
    Args:
        image_path: Path relatif gambar (dari database)
    
    Returns:
        True jika berhasil dihapus
    """
    # Bangun path absolut
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    full_path = os.path.join(base_dir, image_path)
    
    if os.path.exists(full_path):
        os.remove(full_path)
        return True
    return False
