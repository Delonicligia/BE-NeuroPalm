from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "petani"
    ADMIN = "admin"
    
class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER 
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
class UserUpdate(BaseModel):
    username: str = Field(None, max_length=50)
    email: EmailStr = None
    password: str = Field(None, min_length=6)
    role: UserRole = None
        
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: str
    role: UserRole