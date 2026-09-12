"""GridSignal model — data-spec.md SS8. Owned by P1 (grid.py writes it)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GridSignal(Base):
    __tablename__ = "grid_signals"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: f"SIG-{uuid.uuid4().hex[:8]}"
    )
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    condition: Mapped[str] = mapped_column(String)  # GridCondition
    recommended_ev_load_kw: Mapped[float] = mapped_column(Float)
    signal_operator: Mapped[str] = mapped_column(String)  # SignalOperator
    renewable_availability: Mapped[str] = mapped_column(String)  # RenewableAvailability
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
