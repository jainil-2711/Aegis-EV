"""Driver recommendation service (P3)."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Principal
from app.models.charging_schedule_entry import ChargingScheduleEntry
from app.models.energy_slot import EnergySlot
from app.engine.green_score import calculate_green_score
from app.models.optimization_run import OptimizationRun
from app.schemas.driver import DriverRecommendationResponse
from app.services.driver.authorization import get_authorized_ev
from app.services.optimization.optimizer import get_active_run


class NoActiveScheduleError(Exception):
    """Raised when no active/applied optimization schedule is available."""


def _entries_for_run(db: Session, run_id: str, ev_id: str) -> list[ChargingScheduleEntry]:
    return list(
        db.execute(
            select(ChargingScheduleEntry)
            .where(
                ChargingScheduleEntry.optimization_run_id == run_id,
                ChargingScheduleEntry.ev_id == ev_id,
                ChargingScheduleEntry.charging_power_kw > 0,
            )
            .order_by(ChargingScheduleEntry.timestamp.asc())
        ).scalars().all()
    )


def get_driver_recommendation(
    db: Session, principal: Principal, ev_id: str | None = None
) -> DriverRecommendationResponse:
    ev = get_authorized_ev(db, principal, ev_id)

    run = get_active_run(db)
    if run is None:
        raise NoActiveScheduleError(
            "No active optimization schedule is available yet. The network operator must apply an optimization schedule first."
        )

    entries = _entries_for_run(db, run.id, ev.id)
    if not entries:
        raise NoActiveScheduleError(f"No schedule entries for {ev.id} in run {run.id}.")

    total_energy_kwh = sum(e.energy_kwh for e in entries)
    total_cost = sum(e.cost for e in entries)
    total_renewable_kwh = sum(e.renewable_energy_kwh for e in entries)
    total_co2_kg = sum(e.co2_kg for e in entries)
    renewable_share_pct = (total_renewable_kwh / total_energy_kwh * 100.0) if total_energy_kwh else 0.0
    price_per_kwh = (total_cost / total_energy_kwh) if total_energy_kwh else 0.0
    slot_rows = list(db.execute(select(EnergySlot).where(EnergySlot.timestamp.in_([e.timestamp for e in entries]))).scalars().all())
    slot_map = {row.timestamp: row for row in slot_rows}
    weighted_carbon = sum(e.grid_energy_kwh * slot_map[e.timestamp].carbon_intensity for e in entries if e.timestamp in slot_map)
    average_carbon = weighted_carbon / total_energy_kwh if total_energy_kwh else 0.0
    green_score = calculate_green_score(
        renewable_share_pct=renewable_share_pct,
        average_carbon_intensity=average_carbon,
        grid_energy_kwh=sum(e.grid_energy_kwh for e in entries),
        total_energy_kwh=total_energy_kwh,
    )

    return DriverRecommendationResponse(
        optimization_run_id=run.id,
        window_start=entries[0].timestamp,
        window_end=entries[-1].timestamp + timedelta(minutes=30),
        estimated_cost=round(total_cost, 2),
        price_per_kwh=round(price_per_kwh, 2),
        renewable_share_pct=round(renewable_share_pct, 1),
        co2_impact_kg=round(total_co2_kg, 2),
        green_score=green_score,
        why=_build_why(renewable_share_pct, run.mode, green_score),
    )


def _build_why(renewable_share_pct: float, mode: str, green_score: float) -> str:
    if renewable_share_pct >= 60:
        return (
            f"Aegis selected this window from the active {mode} network schedule: "
            f"{renewable_share_pct:.0f}% renewable alignment, while keeping your charging target feasible. "
            f"Green Score: {green_score:.0f}/100."
        )
    if renewable_share_pct >= 30:
        return (
            f"Aegis found a feasible balance between renewable availability and the {mode} network objective. "
            f"The active schedule gives {renewable_share_pct:.0f}% renewable alignment and a Green Score of {green_score:.0f}/100."
        )
    return (
        f"Renewable availability is limited in your feasible window, so Aegis follows the {mode} network objective "
        f"while respecting your charging constraints. Green Score: {green_score:.0f}/100."
    )