from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class SawitBase(BaseModel):
    tingkat_kematangan: str = Field(..., max_length=100)
    warna_dominan: str = Field(..., max_length=255)
    persentase: str = Field(..., max_length=255)

class SawitCreate(SawitBase):
    gambar_sawit: str = Field(..., max_length=255)

class SawitUpdate(BaseModel):
    gambar_sawit: Optional[str] = Field(None, max_length=255)
    tingkat_kematangan: Optional[str] = Field(None, max_length=100)
    warna_dominan: Optional[str] = Field(None, max_length=255)
    persentase: Optional[str] = Field(None, max_length=255)

class SawitResponse(SawitBase):
    id: int
    user_id: int
    gambar_sawit: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
