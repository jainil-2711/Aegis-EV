"""
OptimizationRun model — data-spec.md SS11.

Owned by P2. Declared here as part of the shared model foundation so P1's
ev_load.py (architecture.md SS4) can query the active applied run without
waiting on P2's service code. P2 owns all writes to this table.
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
    mode: Mapped[str] = mapped_column(String)  # OperatorObjective
    baseline_peak_kw: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_peak_kw: Mapped[float] = mapped_column(Float, default=0.0)
    baseline_cost: Mapped[float] = mapped_column(Float, default=0.0)
    optimized_cost: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="pending")  # OptimizationStatus
