"""Charging network operator status and impact services (P4)."""

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models.ev import EV
from app.schemas.operator import NetworkImpactResponse, NetworkStatusResponse
from app.schemas.shared import BeforeAfter, EVLoad
from app.services.grid.status import build_grid_status
from app.services.optimization.optimizer import get_active_or_latest_run, get_run_metrics
from app.services.shared.ev_load import get_ev_load
from app.services.shared.simulation_clock import current_demo_timestamp
from app.engine.pricing import get_current_pricing_rule


class NoActiveScheduleError(Exception):
    """Raised when no optimization run exists for network impact."""


def _active_counts(db: Session, settings: Settings) -> tuple[int, int]:
    now = current_demo_timestamp(settings)
    evs = db.query(EV).all()
    active_evs = [
        ev
        for ev in evs
        if ev.arrival_time <= now <= ev.departure_time and ev.current_soc < ev.target_soc
    ]
    active_chargers = {ev.charger_id for ev in active_evs}
    return len(active_evs), len(active_chargers)


def get_network_status(
    db: Session, settings: Settings | None = None
) -> NetworkStatusResponse:
    settings = settings or get_settings()
    grid = build_grid_status(db, settings)
    load = get_ev_load(db, settings)
    active_evs, active_chargers = _active_counts(db, settings)

    renewable_pct = (
        min(100.0, max(0.0, grid.renewable_generation_kw / grid.grid_demand_kw * 100.0))
        if grid.grid_demand_kw > 0
        else 0.0
    )

    return NetworkStatusResponse(
        active_evs=active_evs,
        active_chargers=active_chargers,
        ev_load=EVLoad(
            current_ev_load_kw=load.current_ev_load_kw,
            scheduled_ev_load_kw=load.scheduled_ev_load_kw,
            peak_ev_load_kw=load.peak_ev_load_kw,
        ),
        renewable_availability_pct=round(renewable_pct, 1),
        grid_demand_kw=grid.grid_demand_kw,
        grid_capacity_kw=grid.grid_capacity_kw,
        renewable_generation_kw=grid.renewable_generation_kw,
    )


def get_network_impact(db: Session) -> NetworkImpactResponse:
    run = get_active_or_latest_run(db)
    if run is None:
        raise NoActiveScheduleError(
            "No optimization run available yet. Run POST /api/optimization/run first."
        )

    baseline, candidate = get_run_metrics(db, get_settings(), run)
    pricing_rule = get_current_pricing_rule(db)

    return NetworkImpactResponse(
        peak_load_kw=BeforeAfter(before=baseline.peak_kw, after=candidate.peak_kw),
        cost=BeforeAfter(before=baseline.cost, after=candidate.cost),
        renewable_share_pct=BeforeAfter(
            before=baseline.renewable_share_pct,
            after=candidate.renewable_share_pct,
        ),
        co2_kg=BeforeAfter(before=baseline.co2_kg, after=candidate.co2_kg),
        pricing_rule=pricing_rule,
        active_optimization_run_id=run.id,
    )
