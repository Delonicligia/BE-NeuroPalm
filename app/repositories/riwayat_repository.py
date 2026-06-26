from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.riwayat_model import Riwayat


class RiwayatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_riwayat(
        self, 
        user_id: int, 
        sawit_id: int, 
        username: str, 
        gambar_sawit: str, 
        tingkat_kematangan: str, 
        warna_dominan: str, 
        persentase: str
    ) -> Riwayat:
        new_riwayat = Riwayat(
            user_id=user_id,
            sawit_id=sawit_id,
            username=username,
            gambar_sawit=gambar_sawit,
            tingkat_kematangan=tingkat_kematangan,
            warna_dominan=warna_dominan,
            persentase=persentase
        )
        self.db.add(new_riwayat)
        await self.db.commit()
        await self.db.refresh(new_riwayat)
        return new_riwayat

    async def get_riwayat_by_id(self, riwayat_id: int) -> Riwayat:
        result = await self.db.execute(select(Riwayat).where(Riwayat.id == riwayat_id))
        return result.scalars().first()

    async def get_all_riwayat(self) -> list[Riwayat]:
        result = await self.db.execute(select(Riwayat))
        return result.scalars().all()

    async def get_riwayat_by_user_id(self, user_id: int) -> list[Riwayat]:
        result = await self.db.execute(select(Riwayat).where(Riwayat.user_id == user_id))
        return result.scalars().all()

    async def update_riwayat(self, riwayat_id: int, update_data: dict) -> Riwayat:
        riwayat = await self.get_riwayat_by_id(riwayat_id)
        if not riwayat:
            return None
        for field, value in update_data.items():
            setattr(riwayat, field, value)
        await self.db.commit()
        await self.db.refresh(riwayat)
        return riwayat

    async def delete_riwayat(self, riwayat_id: int) -> bool:
        riwayat = await self.get_riwayat_by_id(riwayat_id)
        if not riwayat:
            return False
        await self.db.delete(riwayat)
        await self.db.commit()
        return True
