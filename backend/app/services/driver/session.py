"""Driver session and preference service (P3)."""

from sqlalchemy.orm import Session

from app.models.ev import EV
from app.schemas.driver import DriverPreferencesUpdate, DriverSessionResponse
from app.schemas.enums import Flexibility

from app.services.shared.simulation_clock import current_demo_timestamp
from app.config import get_settings

DEMO_EV_ID = "EV-101"


def _get_demo_ev(db: Session) -> EV:
    ev = db.query(EV).filter(EV.id == DEMO_EV_ID).first()
    if ev is None:
        ev = db.query(EV).order_by(EV.id.asc()).first()
    if ev is None:
        raise LookupError("No seeded EV data found. Has scripts/seed_demo.py run?")
    return ev


def _required_energy_kwh(ev: EV) -> float:
    return max(
        ev.battery_capacity_kwh * (ev.target_soc - ev.current_soc) / 100.0 / max(ev.efficiency, 0.01),
        0.0,
    )


def _compute_flexibility(ev: EV) -> Flexibility:
    """Recompute stored flexibility only after driver edits its inputs."""
    effective_power = ev.max_charge_kw
    window_hours = (ev.departure_time - ev.arrival_time).total_seconds() / 3600.0
    if effective_power <= 0 or window_hours <= 0:
        return Flexibility.non_flexible
    required_hours = _required_energy_kwh(ev) / effective_power
    if required_hours >= window_hours:
        return Flexibility.non_flexible
    slack_ratio = (window_hours - required_hours) / window_hours
    if slack_ratio >= 0.66:
        return Flexibility.high
    if slack_ratio >= 0.33:
        return Flexibility.medium
    return Flexibility.low


def _to_response(ev: EV) -> DriverSessionResponse:
    return DriverSessionResponse(
        ev_id=ev.id,
        battery_capacity_kwh=ev.battery_capacity_kwh,
        current_soc=ev.current_soc,
        target_soc=ev.target_soc,
        arrival_time=ev.arrival_time,
        departure_time=ev.departure_time,
        max_charge_kw=ev.max_charge_kw,
        efficiency=ev.efficiency,
        preference=ev.preference,
        charger_id=ev.charger_id,
        flexibility=ev.flexibility,
    )


def get_driver_session(db: Session) -> DriverSessionResponse:
    ev = _get_demo_ev(db)
    return _to_response(ev)


def update_driver_preferences(
    db: Session, update: DriverPreferencesUpdate
) -> DriverSessionResponse:
    ev = _get_demo_ev(db)

    if update.target_soc is not None and update.target_soc < ev.current_soc:
        raise ValueError("target_soc cannot be below current_soc")
    if update.departure_time is not None and update.departure_time <= ev.arrival_time:
        raise ValueError("departure_time must be after arrival_time")

    ev.preference = update.preference.value
    if update.target_soc is not None:
        ev.target_soc = update.target_soc
    if update.departure_time is not None:
        ev.departure_time = update.departure_time

    # Keep P1's stored derived field consistent when its source inputs change.
    ev.flexibility = _compute_flexibility(ev).value

    db.add(ev)
    db.commit()
    db.refresh(ev)
    return _to_response(ev)
