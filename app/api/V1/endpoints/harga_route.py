from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_db
from app.schemas.harga_schema import HargaCreate, HargaResponse, HargaUpdate
from app.services.harga_service import HargaService
from app.core.get_current import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/harga", tags=["harga"])

@router.post("/", response_model=HargaResponse, status_code=status.HTTP_201_CREATED)
async def create_harga(
    harga_create: HargaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk membuat data harga sawit baru.
    Hanya bisa diakses oleh Admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin yang diperbolehkan membuat data harga sawit"
        )
    harga_service = HargaService(db)
    return await harga_service.create_harga(
        user_id=current_user.id,
        harga_create=harga_create
    )

@router.get("/", response_model=List[HargaResponse])
async def get_all_harga(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mendapatkan daftar harga sawit.
    Semua role dapat melihat seluruh data harga sawit.
    """
    harga_service = HargaService(db)
    return await harga_service.get_all_harga()

@router.get("/{harga_id}", response_model=HargaResponse)
async def get_harga_by_id(
    harga_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mendapatkan detail data harga sawit berdasarkan ID.
    Semua role dapat melihat detail data harga sawit.
    """
    harga_service = HargaService(db)
    return await harga_service.get_harga_by_id(harga_id)

@router.put("/{harga_id}", response_model=HargaResponse)
async def update_harga(
    harga_id: int,
    harga_update: HargaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mengubah data harga sawit.
    Hanya admin yang diperbolehkan mengubah data harga sawit.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin yang diperbolehkan mengubah data harga sawit"
        )
    harga_service = HargaService(db)
    return await harga_service.update_harga(
        harga_id=harga_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        harga_update=harga_update
    )

@router.delete("/{harga_id}", status_code=status.HTTP_200_OK)
async def delete_harga(
    harga_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk menghapus data harga sawit.
    Hanya admin yang diperbolehkan menghapus data harga sawit.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin yang diperbolehkan menghapus data harga sawit"
        )
    harga_service = HargaService(db)
    await harga_service.delete_harga(
        harga_id=harga_id,
        current_user_id=current_user.id,
        current_user_role=current_user.role
    )
    return {"message": "Harga record deleted successfully"}
