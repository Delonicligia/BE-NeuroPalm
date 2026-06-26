from datetime import datetime
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import base
from enum import Enum
from typing import List

class UserRole(Enum):
    USER = "petani"
    ADMIN = "admin"

class User(base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default=UserRole.USER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now(), onupdate=func.now())

    sawit: Mapped[List["Sawit"]] = relationship("Sawit", back_populates="user")
    harga: Mapped[List["Harga"]] = relationship("Harga", back_populates="user")
    riwayat: Mapped[List["Riwayat"]] = relationship("Riwayat", back_populates="user")