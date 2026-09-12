"""
ChargingScheduleEntry model — data-spec.md SS10.

Owned by P2 (written by the optimizer). Declared here so P1's ev_load.py
can read schedule rows for the currently-applied OptimizationRun.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChargingScheduleEntry(Base):
    __tablename__ = "charging_schedule_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    optimization_run_id: Mapped[str] = mapped_column(ForeignKey("optimization_runs.id"))
    ev_id: Mapped[str] = mapped_column(ForeignKey("evs.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    charging_power_kw: Mapped[float] = mapped_column(Float)
    energy_kwh: Mapped[float] = mapped_column(Float)
    renewable_energy_kwh: Mapped[float] = mapped_column(Float)
    grid_energy_kwh: Mapped[float] = mapped_column(Float)
    cost: Mapped[float] = mapped_column(Float)
    co2_kg: Mapped[float] = mapped_column(Float)
