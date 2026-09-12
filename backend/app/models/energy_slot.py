"""EnergySlot model — normalized grid/renewable data for one 30-minute slot."""

from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EnergySlot(Base):
    __tablename__ = "energy_slots"

    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)

    # Grid inputs
    base_load_kw: Mapped[float] = mapped_column(Float)
    grid_capacity_kw: Mapped[float] = mapped_column(Float)

    solar_generation_kw: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0.0",
        nullable=False,
    )

    wind_generation_kw: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0.0",
        nullable=False,
    )

    renewable_kw: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0.0",
        nullable=False,
    )

    # Energy/economic context
    electricity_price: Mapped[float] = mapped_column(Float)
    carbon_intensity: Mapped[float] = mapped_column(Float)

    # Data provenance
    source_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    forecast_for: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)