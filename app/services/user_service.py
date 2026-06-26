from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.core.hash_password import hash_password, verify_password
from app.core.token import create_access_token, verify_access_token
from app.core.config import settings
from datetime import timedelta

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)

    async def register_user(self, user_create: UserCreate) -> UserResponse:
        existing_email = await self.user_repository.get_user_by_email(user_create.email)
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
        existing_username = await self.user_repository.get_user_by_username(user_create.username)
        if existing_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
        
        hashed_password = hash_password(user_create.password)
        user_create.password = hashed_password
        new_user = await self.user_repository.create_user(user_create)
        return UserResponse.from_orm(new_user)

    async def login_user(self, user_login: UserLogin) -> Token:
        user = await self.user_repository.get_user_by_email(user_login.email)
        if not user or not verify_password(user_login.password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires)
        return Token(access_token=access_token, token_type="bearer")

    async def get_current_user(self, token: str) -> UserResponse:
        token_data = verify_access_token(token)
        if not token_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        user = await self.user_repository.get_user_by_email(token_data.email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return UserResponse.from_orm(user)

    async def get_all_users(self) -> list[UserResponse]:
        users = await self.user_repository.get_all_users()
        return [UserResponse.model_validate(user) for user in users]

    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserResponse:
        # Ambil data yang diisi saja (exclude_unset)
        update_data = user_update.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided for update")
        
        # Cek duplikat email jika email diubah
        if "email" in update_data:
            existing = await self.user_repository.get_user_by_email(update_data["email"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        
        # Cek duplikat username jika username diubah
        if "username" in update_data:
            existing = await self.user_repository.get_user_by_username(update_data["username"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
        
        # Hash password jika diubah
        if "password" in update_data:
            update_data["password"] = hash_password(update_data["password"])
        
        # Convert role enum ke string value
        if "role" in update_data and hasattr(update_data["role"], "value"):
            update_data["role"] = update_data["role"].value
        
        updated_user = await self.user_repository.update_user(user_id, update_data)
        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return UserResponse.model_validate(updated_user)

    async def delete_user(self, user_id: int) -> bool:
        deleted = await self.user_repository.delete_user(user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return True