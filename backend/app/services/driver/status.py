"""Deterministic simulated-live driver status service (P3)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.charging_schedule_entry import ChargingScheduleEntry
from app.models.charging_session import ChargingSession
from app.models.ev import EV
from app.schemas.driver import DriverSessionStatusResponse
from app.schemas.enums import SessionStatus
from app.services.optimization.optimizer import get_active_run
from app.services.shared.simulation_clock import current_demo_timestamp


def get_session_status(db: Session, ev_id: str) -> DriverSessionStatusResponse:
    ev = db.get(EV, ev_id)
    if ev is None:
        raise LookupError(f"Unknown EV {ev_id}")

    session = db.query(ChargingSession).filter(ChargingSession.ev_id == ev_id).first()
    status = SessionStatus(session.status) if session else SessionStatus.pending

    run = get_active_run(db)
    entries: list[ChargingScheduleEntry] = []
    if run is not None:
        entries = list(
            db.execute(
                select(ChargingScheduleEntry)
                .where(
                    ChargingScheduleEntry.optimization_run_id == run.id,
                    ChargingScheduleEntry.ev_id == ev_id,
                    ChargingScheduleEntry.charging_power_kw > 0,
                )
                .order_by(ChargingScheduleEntry.timestamp.asc())
            ).scalars().all()
        )

    now = current_demo_timestamp(get_settings())
    elapsed = [entry for entry in entries if entry.timestamp <= now]
    energy_so_far = sum(e.energy_kwh for e in elapsed)
    renewable_so_far = sum(e.renewable_energy_kwh for e in elapsed)
    cost_so_far = sum(e.cost for e in elapsed)
    co2_so_far = sum(e.co2_kg for e in elapsed)

    current_entry = elapsed[-1] if elapsed else None
    charging_power_kw = current_entry.charging_power_kw if current_entry else 0.0
    renewable_share_pct = renewable_so_far / energy_so_far * 100.0 if energy_so_far else 0.0
    grid_share_pct = max(0.0, 100.0 - renewable_share_pct) if energy_so_far else 0.0
    current_soc = _project_soc(ev, energy_so_far)

    if entries and len(elapsed) == len(entries) and elapsed:
        status = SessionStatus.completed
    elif elapsed and status == SessionStatus.scheduled:
        status = SessionStatus.charging

    return DriverSessionStatusResponse(
        status=status,
        current_soc=round(current_soc, 1),
        charging_power_kw=round(charging_power_kw, 2),
        renewable_share_pct=round(renewable_share_pct, 1),
        grid_share_pct=round(grid_share_pct, 1),
        cost_so_far=round(cost_so_far, 2),
        co2_kg_so_far=round(co2_so_far, 2),
        green_score=None,
        simulated=True,
        updated_at=now,
    )


def _project_soc(ev: EV, energy_delivered_kwh: float) -> float:
    soc_gain_pct = (
        energy_delivered_kwh * ev.efficiency / ev.battery_capacity_kwh * 100.0
        if ev.battery_capacity_kwh > 0
        else 0.0
    )
    return min(ev.current_soc + soc_gain_pct, ev.target_soc)
