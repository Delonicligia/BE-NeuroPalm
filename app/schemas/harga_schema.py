from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class HargaBase(BaseModel):
    harga_perkg: str = Field(..., max_length=255)
    keterangan: str = Field(..., max_length=255)

class HargaCreate(HargaBase):
    pass

class HargaUpdate(BaseModel):
    harga_perkg: Optional[str] = Field(None, max_length=255)
    keterangan: Optional[str] = Field(None, max_length=255)

class HargaResponse(HargaBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
