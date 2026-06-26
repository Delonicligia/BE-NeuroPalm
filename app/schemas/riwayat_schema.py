from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RiwayatBase(BaseModel):
    gambar_sawit: str = Field(..., max_length=255)
    tingkat_kematangan: str = Field(..., max_length=100)
    warna_dominan: str = Field(..., max_length=255)
    persentase: str = Field(..., max_length=255)
    username: str = Field(..., max_length=50)

class RiwayatCreate(RiwayatBase):
    sawit_id: int

class RiwayatUpdate(BaseModel):
    gambar_sawit: Optional[str] = Field(None, max_length=255)
    tingkat_kematangan: Optional[str] = Field(None, max_length=100)
    warna_dominan: Optional[str] = Field(None, max_length=255)
    persentase: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, max_length=50)
    sawit_id: Optional[int] = None

class RiwayatResponse(RiwayatBase):
    id: int
    user_id: int
    sawit_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
