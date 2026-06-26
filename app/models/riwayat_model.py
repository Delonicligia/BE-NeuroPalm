from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import base


class Riwayat(base):
    __tablename__ = "riwayat_klasifikasi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    gambar_sawit: Mapped[str] = mapped_column(String(255))
    tingkat_kematangan: Mapped[str] = mapped_column(String(100))
    warna_dominan: Mapped[str] = mapped_column(String(255))
    persentase: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now(), onupdate=func.now())

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="riwayat")

    sawit_id: Mapped[int] = mapped_column(Integer, ForeignKey("sawit.id"), nullable=False)
    sawit: Mapped["Sawit"] = relationship("Sawit", back_populates="riwayat")
