from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_db
from app.schemas.riwayat_schema import RiwayatCreate, RiwayatResponse, RiwayatUpdate
from app.services.riwayat_service import RiwayatService
from app.core.get_current import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/riwayat", tags=["riwayat"])

@router.post("/", response_model=RiwayatResponse, status_code=status.HTTP_201_CREATED)
async def create_riwayat(
    riwayat_create: RiwayatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk membuat/mencatat riwayat klasifikasi baru.
    """
    riwayat_service = RiwayatService(db)
    return await riwayat_service.create_riwayat(
        user_id=current_user.id,
        username=current_user.username,
        riwayat_create=riwayat_create
    )

@router.get("/", response_model=List[RiwayatResponse])
async def get_all_riwayat(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mendapatkan daftar riwayat klasifikasi.
    - Admin mendapatkan semua data riwayat klasifikasi.
    - Petani/User hanya mendapatkan data riwayat miliknya sendiri.
    """
    riwayat_service = RiwayatService(db)
    if current_user.role == "admin":
        return await riwayat_service.get_all_riwayat()
    return await riwayat_service.get_riwayat_by_user_id(current_user.id)

@router.get("/{riwayat_id}", response_model=RiwayatResponse)
async def get_riwayat_by_id(
    riwayat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mendapatkan detail riwayat klasifikasi berdasarkan ID.
    Hanya pemilik data atau admin yang dapat mengakses detail data ini.
    """
    riwayat_service = RiwayatService(db)
    riwayat = await riwayat_service.get_riwayat_by_id(riwayat_id)
    
    # Validasi kepemilikan/otoritas
    if riwayat.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this record"
        )
    return riwayat

@router.put("/{riwayat_id}", response_model=RiwayatResponse)
async def update_riwayat(
    riwayat_id: int,
    riwayat_update: RiwayatUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mengubah data riwayat klasifikasi.
    Hanya pemilik data atau admin yang dapat mengubah data ini.
    """
    riwayat_service = RiwayatService(db)
    return await riwayat_service.update_riwayat(
        riwayat_id=riwayat_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        riwayat_update=riwayat_update
    )

@router.delete("/{riwayat_id}", status_code=status.HTTP_200_OK)
async def delete_riwayat(
    riwayat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk menghapus data riwayat klasifikasi.
    Hanya pemilik data atau admin yang dapat menghapus data ini.
    """
    riwayat_service = RiwayatService(db)
    await riwayat_service.delete_riwayat(
        riwayat_id=riwayat_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role
    )
    return {"message": "Riwayat record deleted successfully"}
