"""
GreenCharge — Grid status/forecast service (P1)

Combines the current EnergySlot with the shared EV load figures
(services/shared/ev_load.py) into the GridStatusResponse shape. Does not
duplicate EV-load computation — that would violate architecture.md SS4.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.energy_slot import EnergySlot as EnergySlotModel
from app.schemas.grid import GridStatusResponse
from app.schemas.shared import EVLoad
from app.services.shared.ev_load import get_ev_load
from app.services.shared.simulation_clock import current_demo_timestamp


def _current_slot(db: Session, settings: Settings, now: datetime | None) -> EnergySlotModel | None:
    ts = current_demo_timestamp(settings, now)
    return db.get(EnergySlotModel, ts)


def build_grid_status(
    db: Session, settings: Settings, now: datetime | None = None
) -> GridStatusResponse:
    slot = _current_slot(db, settings, now)
    ev_load_result = get_ev_load(db, settings, now)

    if slot is None:
        # Dataset not seeded yet — return a clearly-zeroed response rather
        # than raising, so /api/health-adjacent smoke checks don't 500
        # before scripts/seed_demo.py has run.
        return GridStatusResponse(
            grid_demand_kw=0.0,
            grid_capacity_kw=0.0,
            renewable_generation_kw=0.0,
            ev_load=EVLoad(
                current_ev_load_kw=0.0, scheduled_ev_load_kw=0.0, peak_ev_load_kw=0.0
            ),
            headroom_kw=0.0,
        )

    grid_demand_kw = round(slot.base_load_kw + ev_load_result.current_ev_load_kw, 1)
    headroom_kw = round(slot.grid_capacity_kw - grid_demand_kw, 1)

    return GridStatusResponse(
        grid_demand_kw=grid_demand_kw,
        grid_capacity_kw=slot.grid_capacity_kw,
        renewable_generation_kw=slot.renewable_kw,
        ev_load=EVLoad(
            current_ev_load_kw=ev_load_result.current_ev_load_kw,
            scheduled_ev_load_kw=ev_load_result.scheduled_ev_load_kw,
            peak_ev_load_kw=ev_load_result.peak_ev_load_kw,
        ),
        headroom_kw=headroom_kw,
    )


def list_forecast_slots(db: Session) -> list[EnergySlotModel]:
    stmt = select(EnergySlotModel).order_by(EnergySlotModel.timestamp.asc())
    return list(db.execute(stmt).scalars().all())
