from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.riwayat_repository import RiwayatRepository
from app.schemas.riwayat_schema import RiwayatCreate, RiwayatResponse, RiwayatUpdate

class RiwayatService:
    def __init__(self, db: AsyncSession):
        self.riwayat_repository = RiwayatRepository(db)

    async def create_riwayat(self, user_id: int, username: str, riwayat_create: RiwayatCreate) -> RiwayatResponse:
        new_riwayat = await self.riwayat_repository.create_riwayat(
            user_id=user_id,
            sawit_id=riwayat_create.sawit_id,
            username=username,
            gambar_sawit=riwayat_create.gambar_sawit,
            tingkat_kematangan=riwayat_create.tingkat_kematangan,
            warna_dominan=riwayat_create.warna_dominan,
            persentase=riwayat_create.persentase
        )
        return RiwayatResponse.model_validate(new_riwayat)

    async def get_riwayat_by_id(self, riwayat_id: int) -> RiwayatResponse:
        riwayat = await self.riwayat_repository.get_riwayat_by_id(riwayat_id)
        if not riwayat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riwayat record not found")
        return RiwayatResponse.model_validate(riwayat)

    async def get_all_riwayat(self) -> List[RiwayatResponse]:
        riwayats = await self.riwayat_repository.get_all_riwayat()
        return [RiwayatResponse.model_validate(r) for r in riwayats]

    async def get_riwayat_by_user_id(self, user_id: int) -> List[RiwayatResponse]:
        riwayats = await self.riwayat_repository.get_riwayat_by_user_id(user_id)
        return [RiwayatResponse.model_validate(r) for r in riwayats]

    async def update_riwayat(
        self,
        riwayat_id: int,
        current_user_id: int,
        current_user_role: str,
        riwayat_update: RiwayatUpdate
    ) -> RiwayatResponse:
        riwayat = await self.riwayat_repository.get_riwayat_by_id(riwayat_id)
        if not riwayat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riwayat record not found")

        # Validasi kepemilikan/otoritas (hanya pemilik atau admin yang bisa update)
        if riwayat.user_id != current_user_id and current_user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this record"
            )

        update_data = riwayat_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided for update")

        updated_riwayat = await self.riwayat_repository.update_riwayat(riwayat_id, update_data)
        return RiwayatResponse.model_validate(updated_riwayat)

    async def delete_riwayat(self, riwayat_id: int, current_user_id: int, current_user_role: str) -> bool:
        riwayat = await self.riwayat_repository.get_riwayat_by_id(riwayat_id)
        if not riwayat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riwayat record not found")

        # Validasi kepemilikan/otoritas (hanya pemilik atau admin yang bisa hapus)
        if riwayat.user_id != current_user_id and current_user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this record"
            )

        await self.riwayat_repository.delete_riwayat(riwayat_id)
        return True
