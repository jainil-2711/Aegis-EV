"""Driver recommendation service (P3)."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.charging_schedule_entry import ChargingScheduleEntry
from app.models.ev import EV
from app.models.optimization_run import OptimizationRun
from app.schemas.driver import DriverRecommendationResponse
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


def get_driver_recommendation(db: Session, ev_id: str) -> DriverRecommendationResponse:
    ev = db.get(EV, ev_id)
    if ev is None:
        raise NoActiveScheduleError(f"Unknown EV {ev_id}.")

    run = get_active_run(db)
    if run is None:
        raise NoActiveScheduleError(
            "No active optimization schedule is available yet. The network operator must apply an optimization schedule first."
        )

    entries = _entries_for_run(db, run.id, ev_id)
    if not entries:
        raise NoActiveScheduleError(f"No schedule entries for {ev_id} in run {run.id}.")

    total_energy_kwh = sum(e.energy_kwh for e in entries)
    total_cost = sum(e.cost for e in entries)
    total_renewable_kwh = sum(e.renewable_energy_kwh for e in entries)
    total_co2_kg = sum(e.co2_kg for e in entries)
    renewable_share_pct = (total_renewable_kwh / total_energy_kwh * 100.0) if total_energy_kwh else 0.0
    price_per_kwh = (total_cost / total_energy_kwh) if total_energy_kwh else 0.0

    return DriverRecommendationResponse(
        optimization_run_id=run.id,
        window_start=entries[0].timestamp,
        window_end=entries[-1].timestamp + timedelta(minutes=30),
        estimated_cost=round(total_cost, 2),
        price_per_kwh=round(price_per_kwh, 2),
        renewable_share_pct=round(renewable_share_pct, 1),
        co2_impact_kg=round(total_co2_kg, 2),
        green_score=None,
        why=_build_why(renewable_share_pct, run.mode),
    )


def _build_why(renewable_share_pct: float, mode: str) -> str:
    if renewable_share_pct >= 60:
        return (
            "This window aligns strongly with renewable availability while meeting "
            f"your charging requirements under the {mode} network objective."
        )
    if renewable_share_pct >= 30:
        return (
            "This window balances renewable availability, network conditions, and "
            f"your charging requirements under the {mode} network objective."
        )
    return (
        "Renewable availability is limited in the feasible window, so the schedule "
        f"prioritizes the {mode} network objective while respecting your constraints."
    )
