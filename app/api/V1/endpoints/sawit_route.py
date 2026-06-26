from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.database import get_db
from app.schemas.sawit_schema import SawitResponse
from app.services.sawit_service import SawitService
from app.core.get_current import get_current_user
from app.models.user_model import User

from app.core.image_utils import validate_image
from app.services.predict_service import predict_sawit_image

router = APIRouter(prefix="/sawit", tags=["sawit"])

@router.post("/predict", response_model=SawitResponse, status_code=status.HTTP_201_CREATED)
async def predict_sawit(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk memprediksi tingkat kematangan sawit dari gambar menggunakan model ML TFLite
    dan menyimpan hasilnya langsung ke database.
    """
    # Validasi gambar dan baca bytes untuk model
    image_bytes = await validate_image(file)
    
    # Jalankan prediksi model
    tingkat_kematangan, warna_dominan, persentase = predict_sawit_image(image_bytes)
    
    # Simpan data sawit beserta gambar ke database
    sawit_service = SawitService(db)
    sawit_response = await sawit_service.create_sawit(
        user_id=current_user.id,
        file=file,
        tingkat_kematangan=tingkat_kematangan,
        warna_dominan=warna_dominan,
        persentase=persentase
    )

    # Simpan riwayat klasifikasi secara otomatis ke tabel riwayat_klasifikasi
    from app.repositories.riwayat_repository import RiwayatRepository
    riwayat_repository = RiwayatRepository(db)
    await riwayat_repository.create_riwayat(
        user_id=current_user.id,
        sawit_id=sawit_response.id,
        username=current_user.username,
        gambar_sawit=sawit_response.gambar_sawit,
        tingkat_kematangan=tingkat_kematangan,
        warna_dominan=warna_dominan,
        persentase=persentase
    )
    
    return sawit_response

@router.post("/", response_model=SawitResponse, status_code=status.HTTP_201_CREATED)
async def create_sawit(
    file: UploadFile = File(...),
    tingkat_kematangan: str = Form(...),
    warna_dominan: str = Form(...),
    persentase: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk membuat data sawit baru beserta upload gambarnya.
    """
    sawit_service = SawitService(db)
    return await sawit_service.create_sawit(
        user_id=current_user.id,
        file=file,
        tingkat_kematangan=tingkat_kematangan,
        warna_dominan=warna_dominan,
        persentase=persentase
    )

@router.get("/", response_model=List[SawitResponse])
async def get_all_sawit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mendapatkan daftar data sawit.
    - Admin mendapatkan semua data sawit.
    - Petani/User hanya mendapatkan data sawit miliknya sendiri.
    """
    sawit_service = SawitService(db)
    if current_user.role == "admin":
        return await sawit_service.get_all_sawit()
    return await sawit_service.get_sawit_by_user_id(current_user.id)

@router.get("/{sawit_id}", response_model=SawitResponse)
async def get_sawit_by_id(
    sawit_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mendapatkan detail data sawit berdasarkan ID.
    Hanya pemilik data atau admin yang dapat mengakses detail data ini.
    """
    sawit_service = SawitService(db)
    sawit = await sawit_service.get_sawit_by_id(sawit_id)
    
    # Validasi kepemilikan/otoritas
    if sawit.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this record"
        )
    return sawit

@router.put("/{sawit_id}", response_model=SawitResponse)
async def update_sawit(
    sawit_id: int,
    file: Optional[UploadFile] = File(None),
    tingkat_kematangan: Optional[str] = Form(None),
    warna_dominan: Optional[str] = Form(None),
    persentase: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mengubah data sawit beserta gambarnya (opsional).
    Hanya pemilik data atau admin yang dapat mengubah data ini.
    """
    sawit_service = SawitService(db)
    return await sawit_service.update_sawit(
        sawit_id=sawit_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        file=file,
        tingkat_kematangan=tingkat_kematangan,
        warna_dominan=warna_dominan,
        persentase=persentase
    )

@router.delete("/{sawit_id}", status_code=status.HTTP_200_OK)
async def delete_sawit(
    sawit_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk menghapus data sawit beserta gambarnya.
    Hanya pemilik data atau admin yang dapat menghapus data ini.
    """
    sawit_service = SawitService(db)
    await sawit_service.delete_sawit(
        sawit_id=sawit_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role
    )
    return {"message": "Sawit record deleted successfully"}
