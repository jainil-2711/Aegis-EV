"""Station model — data-spec.md SS5. Written by P1's synthetic generator."""

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    capacity_kw: Mapped[float] = mapped_column(Float)
    charger_count: Mapped[int] = mapped_column(Integer)
