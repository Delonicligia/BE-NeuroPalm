from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.sawit_model import Sawit


class SawitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_sawit(self, user_id: int, gambar_sawit: str, tingkat_kematangan: str, warna_dominan: str, persentase: str) -> Sawit:
        new_sawit = Sawit(
            user_id=user_id,
            gambar_sawit=gambar_sawit,
            tingkat_kematangan=tingkat_kematangan,
            warna_dominan=warna_dominan,
            persentase=persentase
        )
        self.db.add(new_sawit)
        await self.db.commit()
        await self.db.refresh(new_sawit)
        return new_sawit

    async def get_sawit_by_id(self, sawit_id: int) -> Sawit:
        result = await self.db.execute(select(Sawit).where(Sawit.id == sawit_id))
        return result.scalars().first()

    async def get_all_sawit(self) -> list[Sawit]:
        result = await self.db.execute(select(Sawit))
        return result.scalars().all()

    async def get_sawit_by_user_id(self, user_id: int) -> list[Sawit]:
        result = await self.db.execute(select(Sawit).where(Sawit.user_id == user_id))
        return result.scalars().all()

    async def update_sawit(self, sawit_id: int, update_data: dict) -> Sawit:
        sawit = await self.get_sawit_by_id(sawit_id)
        if not sawit:
            return None
        for field, value in update_data.items():
            setattr(sawit, field, value)
        await self.db.commit()
        await self.db.refresh(sawit)
        return sawit

    async def delete_sawit(self, sawit_id: int) -> bool:
        sawit = await self.get_sawit_by_id(sawit_id)
        if not sawit:
            return False
        await self.db.delete(sawit)
        await self.db.commit()
        return True
