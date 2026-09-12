"""Aegis optimization run model.

P2 stores a complete metric snapshot at run creation time so historical
candidate/active results remain stable even when later GridSignals change.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: f"RUN-{uuid.uuid4().hex[:8]}"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    mode: Mapped[str] = mapped_column(String)
    scenario: Mapped[str] = mapped_column(String, default="normal")

    # Full immutable metric snapshot for the run. These are populated when the
    # optimizer creates the candidate and are not recalculated from later state.
    baseline_peak_kw: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_peak_kw: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_cost: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_cost: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_renewable_share_pct: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_renewable_share_pct: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_co2_kg: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_co2_kg: Mapped[float] = mapped_column(Float, default=0.0)

    status: Mapped[str] = mapped_column(String, default="pending")
