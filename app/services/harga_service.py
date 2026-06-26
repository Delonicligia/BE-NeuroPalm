from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.harga_repository import HargaRepository
from app.schemas.harga_schema import HargaCreate, HargaResponse, HargaUpdate

class HargaService:
    def __init__(self, db: AsyncSession):
        self.harga_repository = HargaRepository(db)

    async def create_harga(self, user_id: int, harga_create: HargaCreate) -> HargaResponse:
        new_harga = await self.harga_repository.create_harga(
            user_id=user_id,
            harga_perkg=harga_create.harga_perkg,
            keterangan=harga_create.keterangan
        )
        return HargaResponse.model_validate(new_harga)

    async def get_harga_by_id(self, harga_id: int) -> HargaResponse:
        harga = await self.harga_repository.get_harga_by_id(harga_id)
        if not harga:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harga record not found")
        return HargaResponse.model_validate(harga)

    async def get_all_harga(self) -> List[HargaResponse]:
        hargas = await self.harga_repository.get_all_harga()
        return [HargaResponse.model_validate(h) for h in hargas]

    async def get_harga_by_user_id(self, user_id: int) -> List[HargaResponse]:
        hargas = await self.harga_repository.get_harga_by_user_id(user_id)
        return [HargaResponse.model_validate(h) for h in hargas]

    async def update_harga(
        self,
        harga_id: int,
        current_user_id: int,
        current_user_role: str,
        harga_update: HargaUpdate
    ) -> HargaResponse:
        harga = await self.harga_repository.get_harga_by_id(harga_id)
        if not harga:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harga record not found")

        # Validasi kepemilikan/otoritas (hanya pemilik atau admin yang bisa update)
        if harga.user_id != current_user_id and current_user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this record"
            )

        update_data = harga_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided for update")

        updated_harga = await self.harga_repository.update_harga(harga_id, update_data)
        return HargaResponse.model_validate(updated_harga)

    async def delete_harga(self, harga_id: int, current_user_id: int, current_user_role: str) -> bool:
        harga = await self.harga_repository.get_harga_by_id(harga_id)
        if not harga:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Harga record not found")

        # Validasi kepemilikan/otoritas (hanya pemilik atau admin yang bisa hapus)
        if harga.user_id != current_user_id and current_user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this record"
            )

        await self.harga_repository.delete_harga(harga_id)
        return True
