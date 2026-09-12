"""
GreenCharge — Shared EV Load Module (architecture.md SS4)

SINGLE SOURCE OF TRUTH for:
    current_ev_load_kw
    scheduled_ev_load_kw
    peak_ev_load_kw

Both `/api/grid/status` (P1, api/grid.py) and `/api/network/status`
(P4, api/operator.py) MUST call `get_ev_load()` from this module. Neither
endpoint may compute these numbers independently (data-spec.md SS14,
api-contract.md SS13). Authored by P1; read-only for everyone else after
Phase 1 — coordinate any change here (rules.md SS14).

Behavior:
  1. If an OptimizationRun with status == "applied" exists, EV load is
     aggregated from that run's real ChargingScheduleEntry rows. This is
     the normal, post-P2-integration path.
  2. If no applied run exists yet (e.g. during early Phase 1/2 before P2's
     optimizer has produced and the operator has applied anything), a
     clearly-labeled NAIVE FALLBACK estimates load directly from raw EV
     connection windows: an EV contributes its effective charging power
     whenever it is connected and still below target SOC. This fallback
     exists only so /api/grid/status and /api/network/status return
     sensible numbers before Phase 4/5 integration completes — it is not
     the authoritative "baseline" used for before/after impact numbers
     (that baseline lives inside P2's POST /optimization/run handler,
     architecture.md SS6, and is a different concept).
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.charger import Charger
from app.models.charging_schedule_entry import ChargingScheduleEntry
from app.models.ev import EV
from app.models.optimization_run import OptimizationRun
from app.services.shared.simulation_clock import current_demo_timestamp


@dataclass
class EVLoadResult:
    current_ev_load_kw: float
    scheduled_ev_load_kw: float
    peak_ev_load_kw: float
    source: str  # "applied_schedule" | "naive_fallback"


def _latest_applied_run(db: Session) -> OptimizationRun | None:
    stmt = (
        select(OptimizationRun)
        .where(OptimizationRun.status == "applied")
        .order_by(OptimizationRun.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def _from_applied_schedule(
    db: Session, run: OptimizationRun, now: datetime, settings: Settings
) -> EVLoadResult:
    entries = (
        db.execute(
            select(ChargingScheduleEntry).where(
                ChargingScheduleEntry.optimization_run_id == run.id
            )
        )
        .scalars()
        .all()
    )

    by_timestamp: dict[datetime, float] = {}
    for entry in entries:
        by_timestamp[entry.timestamp] = (
            by_timestamp.get(entry.timestamp, 0.0) + entry.charging_power_kw
        )

    if not by_timestamp:
        return EVLoadResult(0.0, 0.0, 0.0, source="applied_schedule")

    sorted_timestamps = sorted(by_timestamp)
    current_ts = current_demo_timestamp(settings, now)

    # Current: exact slot match, else 0 (no scheduled charging right now).
    current_ev_load_kw = by_timestamp.get(current_ts, 0.0)

    # Scheduled: the next slot strictly after "now" — near-term planned
    # load (data-spec.md SS14 "load planned by the active schedule for a
    # selected time"). Falls back to 0 if we're past the last slot.
    future = [ts for ts in sorted_timestamps if ts > current_ts]
    scheduled_ev_load_kw = by_timestamp[future[0]] if future else 0.0

    peak_ev_load_kw = max(by_timestamp.values())

    return EVLoadResult(
        round(current_ev_load_kw, 1),
        round(scheduled_ev_load_kw, 1),
        round(peak_ev_load_kw, 1),
        source="applied_schedule",
    )


def _naive_fallback(db: Session, now: datetime, settings: Settings) -> EVLoadResult:
    evs = db.execute(select(EV)).scalars().all()
    chargers = {c.id: c for c in db.execute(select(Charger)).scalars().all()}

    def connected_load_at(ts: datetime) -> float:
        total = 0.0
        for ev in evs:
            if ev.arrival_time <= ts <= ev.departure_time and ev.current_soc < ev.target_soc:
                charger = chargers.get(ev.charger_id)
                charger_power = charger.max_power_kw if charger else ev.max_charge_kw
                total += min(ev.max_charge_kw, charger_power)
        return total

    current_ts = current_demo_timestamp(settings, now)
    current_ev_load_kw = connected_load_at(current_ts)

    from datetime import timedelta

    next_ts = current_ts + timedelta(minutes=settings.slot_minutes)
    scheduled_ev_load_kw = connected_load_at(next_ts)

    # Peak across the whole 24h horizon, sampled at slot boundaries.
    demo_day = datetime.fromisoformat(settings.demo_day)
    slot_count = int(settings.horizon_hours * 60 / settings.slot_minutes)
    peak_ev_load_kw = max(
        (
            connected_load_at(demo_day + timedelta(minutes=i * settings.slot_minutes))
            for i in range(slot_count)
        ),
        default=0.0,
    )

    return EVLoadResult(
        round(current_ev_load_kw, 1),
        round(scheduled_ev_load_kw, 1),
        round(peak_ev_load_kw, 1),
        source="naive_fallback",
    )


def get_ev_load(db: Session, settings: Settings, now: datetime | None = None) -> EVLoadResult:
    """
    The one function both /api/grid/status and /api/network/status call.
    """
    run = _latest_applied_run(db)
    if run is not None:
        return _from_applied_schedule(db, run, now or datetime.now(), settings)
    return _naive_fallback(db, now or datetime.now(), settings)
