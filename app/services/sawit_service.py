import os
from typing import Optional, List
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.sawit_repository import SawitRepository
from app.schemas.sawit_schema import SawitResponse
from app.core.image_utils import save_image, delete_image

class SawitService:
    def __init__(self, db: AsyncSession):
        self.sawit_repository = SawitRepository(db)

    async def create_sawit(
        self,
        user_id: int,
        file: UploadFile,
        tingkat_kematangan: str,
        warna_dominan: str,
        persentase: str
    ) -> SawitResponse:
        # Simpan gambar menggunakan Pillow helper
        gambar_path = await save_image(file)
        
        # Simpan data ke database melalui repository
        new_sawit = await self.sawit_repository.create_sawit(
            user_id=user_id,
            gambar_sawit=gambar_path,
            tingkat_kematangan=tingkat_kematangan,
            warna_dominan=warna_dominan,
            persentase=persentase
        )
        return SawitResponse.model_validate(new_sawit)

    async def get_sawit_by_id(self, sawit_id: int) -> SawitResponse:
        sawit = await self.sawit_repository.get_sawit_by_id(sawit_id)
        if not sawit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sawit record not found")
        return SawitResponse.model_validate(sawit)

    async def get_all_sawit(self) -> List[SawitResponse]:
        sawits = await self.sawit_repository.get_all_sawit()
        return [SawitResponse.model_validate(s) for s in sawits]

    async def get_sawit_by_user_id(self, user_id: int) -> List[SawitResponse]:
        sawits = await self.sawit_repository.get_sawit_by_user_id(user_id)
        return [SawitResponse.model_validate(s) for s in sawits]

    async def update_sawit(
        self,
        sawit_id: int,
        current_user_id: int,
        current_user_role: str,
        file: Optional[UploadFile] = None,
        tingkat_kematangan: Optional[str] = None,
        warna_dominan: Optional[str] = None,
        persentase: Optional[str] = None
    ) -> SawitResponse:
        sawit = await self.sawit_repository.get_sawit_by_id(sawit_id)
        if not sawit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sawit record not found")
        
        # Validasi kepemilikan/otoritas (hanya pemilik atau admin yang bisa update)
        if sawit.user_id != current_user_id and current_user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this record"
            )

        update_data = {}
        if tingkat_kematangan is not None:
            update_data["tingkat_kematangan"] = tingkat_kematangan
        if warna_dominan is not None:
            update_data["warna_dominan"] = warna_dominan
        if persentase is not None:
            update_data["persentase"] = persentase

        if file is not None:
            # Hapus gambar lama dari penyimpanan
            if sawit.gambar_sawit:
                delete_image(sawit.gambar_sawit)
            # Simpan gambar baru
            gambar_path = await save_image(file)
            update_data["gambar_sawit"] = gambar_path

        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided for update")

        updated_sawit = await self.sawit_repository.update_sawit(sawit_id, update_data)
        return SawitResponse.model_validate(updated_sawit)

    async def delete_sawit(self, sawit_id: int, current_user_id: int, current_user_role: str) -> bool:
        sawit = await self.sawit_repository.get_sawit_by_id(sawit_id)
        if not sawit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sawit record not found")

        # Validasi kepemilikan/otoritas (hanya pemilik atau admin yang bisa hapus)
        if sawit.user_id != current_user_id and current_user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this record"
            )

        # Hapus file gambar dari penyimpanan
        if sawit.gambar_sawit:
            delete_image(sawit.gambar_sawit)

        # Hapus data dari database
        await self.sawit_repository.delete_sawit(sawit_id)
        return True
