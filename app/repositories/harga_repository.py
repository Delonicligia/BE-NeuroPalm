from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.harga_model import Harga


class HargaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_harga(self, user_id: int, harga_perkg: str, keterangan: str) -> Harga:
        new_harga = Harga(
            user_id=user_id,
            harga_perkg=harga_perkg,
            keterangan=keterangan
        )
        self.db.add(new_harga)
        await self.db.commit()
        await self.db.refresh(new_harga)
        return new_harga

    async def get_harga_by_id(self, harga_id: int) -> Harga:
        result = await self.db.execute(select(Harga).where(Harga.id == harga_id))
        return result.scalars().first()

    async def get_all_harga(self) -> list[Harga]:
        result = await self.db.execute(select(Harga))
        return result.scalars().all()

    async def get_harga_by_user_id(self, user_id: int) -> list[Harga]:
        result = await self.db.execute(select(Harga).where(Harga.user_id == user_id))
        return result.scalars().all()

    async def update_harga(self, harga_id: int, update_data: dict) -> Harga:
        harga = await self.get_harga_by_id(harga_id)
        if not harga:
            return None
        for field, value in update_data.items():
            setattr(harga, field, value)
        await self.db.commit()
        await self.db.refresh(harga)
        return harga

    async def delete_harga(self, harga_id: int) -> bool:
        harga = await self.get_harga_by_id(harga_id)
        if not harga:
            return False
        await self.db.delete(harga)
        await self.db.commit()
        return True
