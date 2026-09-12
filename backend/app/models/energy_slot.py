"""EnergySlot model — data-spec.md SS7. Written by P1's synthetic generator.

One row per 30-minute slot across the 24h demo horizon (48 rows/day).
"""

from datetime import datetime

from sqlalchemy import DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EnergySlot(Base):
    __tablename__ = "energy_slots"

    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    base_load_kw: Mapped[float] = mapped_column(Float)
    renewable_kw: Mapped[float] = mapped_column(Float)
    grid_capacity_kw: Mapped[float] = mapped_column(Float)
    electricity_price: Mapped[float] = mapped_column(Float)
    carbon_intensity: Mapped[float] = mapped_column(Float)
