"""
Aegis — Grid status/forecast service (P1)

Builds Grid status from:
    1. the current normalized EnergySlot
    2. the canonical shared EV-load service

Numerical rules:

    renewable_kw = solar_generation_kw + wind_generation_kw
    grid_demand_kw = base_load_kw + ev_load_kw
    headroom_kw = grid_capacity_kw - grid_demand_kw

EV load MUST come from:
    backend/app/services/shared/ev_load.py
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.energy_slot import EnergySlot as EnergySlotModel
from app.schemas.grid import GridStatusResponse
from app.schemas.shared import EVLoad
from app.services.shared.ev_load import get_ev_load
from app.services.shared.simulation_clock import current_demo_timestamp


def _current_slot(
    db: Session,
    settings: Settings,
    now: datetime | None,
) -> EnergySlotModel | None:
    """Return the EnergySlot corresponding to the current demo timestamp."""
    timestamp = current_demo_timestamp(settings, now)
    return db.get(EnergySlotModel, timestamp)


def build_grid_status(
    db: Session,
    settings: Settings,
    now: datetime | None = None,
) -> GridStatusResponse:
    """
    Build the authoritative Grid status.

    The backend is the source of truth for all numerical fields.
    """

    slot = _current_slot(
        db,
        settings,
        now,
    )

    ev_load_result = get_ev_load(
        db,
        settings,
        now,
    )

    # ---------------------------------------------------------------
    # No seeded EnergySlot yet
    # ---------------------------------------------------------------

    if slot is None:
        return GridStatusResponse(
            base_load_kw=0.0,
            solar_generation_kw=0.0,
            wind_generation_kw=0.0,
            renewable_generation_kw=0.0,
            grid_demand_kw=0.0,
            grid_capacity_kw=0.0,
            ev_load=EVLoad(
                current_ev_load_kw=0.0,
                scheduled_ev_load_kw=0.0,
                peak_ev_load_kw=0.0,
            ),
            headroom_kw=0.0,
            source_type="unavailable",
        )

    # ---------------------------------------------------------------
    # Canonical renewable values from EnergySlot
    # ---------------------------------------------------------------

    solar_generation_kw = round(
        max(0.0, slot.solar_generation_kw),
        1,
    )

    wind_generation_kw = round(
        max(0.0, slot.wind_generation_kw),
        1,
    )

    # IMPORTANT:
    # Reconstruct the canonical total from the stored solar/wind values.
    renewable_generation_kw = (
        solar_generation_kw
        + wind_generation_kw
    )

    # ---------------------------------------------------------------
    # EV load
    # ---------------------------------------------------------------

    current_ev_load_kw = round(
        max(
            0.0,
            ev_load_result.current_ev_load_kw,
        ),
        1,
    )

    scheduled_ev_load_kw = round(
        max(
            0.0,
            ev_load_result.scheduled_ev_load_kw,
        ),
        1,
    )

    peak_ev_load_kw = round(
        max(
            0.0,
            ev_load_result.peak_ev_load_kw,
        ),
        1,
    )

    # ---------------------------------------------------------------
    # Grid demand
    # ---------------------------------------------------------------

    base_load_kw = round(
        max(0.0, slot.base_load_kw),
        1,
    )

    grid_capacity_kw = round(
        max(0.0, slot.grid_capacity_kw),
        1,
    )

    grid_demand_kw = round(
        base_load_kw + current_ev_load_kw,
        1,
    )

    headroom_kw = round(
        grid_capacity_kw - grid_demand_kw,
        1,
    )

    return GridStatusResponse(
        base_load_kw=base_load_kw,
        solar_generation_kw=solar_generation_kw,
        wind_generation_kw=wind_generation_kw,
        renewable_generation_kw=round(
            renewable_generation_kw,
            1,
        ),
        grid_demand_kw=grid_demand_kw,
        grid_capacity_kw=grid_capacity_kw,
        ev_load=EVLoad(
            current_ev_load_kw=current_ev_load_kw,
            scheduled_ev_load_kw=scheduled_ev_load_kw,
            peak_ev_load_kw=peak_ev_load_kw,
        ),
        headroom_kw=headroom_kw,
        source_type=slot.source_type or "unknown",
    )


def list_forecast_slots(
    db: Session,
) -> list[EnergySlotModel]:
    """Return all EnergySlots in chronological order."""
    stmt = (
        select(EnergySlotModel)
        .order_by(
            EnergySlotModel.timestamp.asc()
        )
    )

    return list(
        db.execute(stmt)
        .scalars()
        .all()
    )