"""
GreenCharge — Grid signal service (P1)

A GridSignal is a quantitative, advisory system-level signal
(PRD.md SS7, architecture.md SS9). It is normally an optimization
*signal*, never a physical hard constraint — P2's optimizer may weight it
in the objective, but must never treat it as infeasible-if-violated.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.grid_signal import GridSignal as GridSignalModel
from app.schemas.grid import GridSignalCreate


def create_signal(db: Session, payload: GridSignalCreate) -> GridSignalModel:
    signal = GridSignalModel(
        start_time=payload.start_time,
        end_time=payload.end_time,
        condition=payload.condition.value,
        recommended_ev_load_kw=payload.recommended_ev_load_kw,
        signal_operator=payload.signal_operator.value,
        renewable_availability=payload.renewable_availability.value,
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


def list_signals(db: Session, limit: int = 50) -> list[GridSignalModel]:
    stmt = select(GridSignalModel).order_by(GridSignalModel.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())
