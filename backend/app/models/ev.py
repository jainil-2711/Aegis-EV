"""EV model — data-spec.md SS3. Written by P1's synthetic generator."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EV(Base):
    __tablename__ = "evs"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. "EV-104"
    battery_capacity_kwh: Mapped[float] = mapped_column(Float)
    current_soc: Mapped[float] = mapped_column(Float)
    target_soc: Mapped[float] = mapped_column(Float)
    arrival_time: Mapped[datetime] = mapped_column(DateTime)
    departure_time: Mapped[datetime] = mapped_column(DateTime)
    max_charge_kw: Mapped[float] = mapped_column(Float)
    efficiency: Mapped[float] = mapped_column(Float)
    preference: Mapped[str] = mapped_column(String)  # DriverPreference
    charger_id: Mapped[str] = mapped_column(ForeignKey("chargers.id"))

    # Derived, but stored for fast lookup (data-spec.md SS4). Recomputed by
    # the generator at seed time; not mutated by the optimizer.
    flexibility: Mapped[str] = mapped_column(String)

    # Demo-only metadata, not part of the public API contract.
    profile: Mapped[str] = mapped_column(String, default="commuter")
    data_source: Mapped[str] = mapped_column(String, default="synthetic")
