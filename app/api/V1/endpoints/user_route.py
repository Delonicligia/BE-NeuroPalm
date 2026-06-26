from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_db
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse, Token, UserUpdate, UserRole
from app.services.user_service import UserService
from app.core.token import verify_access_token
from app.core.get_current import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    """
    Endpoint untuk mendapatkan semua data user
    """
    user_service = UserService(db)
    return await user_service.get_all_users()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    return await user_service.register_user(user_create)    

@router.post("/login", response_model=Token)
async def login_user(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    return await user_service.login_user(user_login)

@router.get("/me", response_model=UserResponse)
async def get_current_logged_in_user(current_user: User = Depends(get_current_user)):
    """
    Endpoint untuk memeriksa informasi user yang sedang login saat ini
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk update data user yang sedang login saat ini.
    Menghindari perubahan role jika pengubah bukan admin.
    """
    # Jika bukan admin, pastikan role tidak diubah
    if current_user.role != "admin":
        user_update.role = None
        
    user_service = UserService(db)
    return await user_service.update_user(current_user.id, user_update)

@router.put("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk mengubah role user. Hanya bisa diakses oleh Admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin yang dapat mengubah role user"
        )
    user_service = UserService(db)
    user_update = UserUpdate(role=role)
    return await user_service.update_user(user_id, user_update)

@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint untuk menghapus akun user yang sedang login saat ini
    """
    user_service = UserService(db)
    await user_service.delete_user(current_user.id)
    return {"message": "User deleted successfully"}
