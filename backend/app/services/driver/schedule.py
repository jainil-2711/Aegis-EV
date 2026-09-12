"""Driver accept/override service (P3)."""

from sqlalchemy.orm import Session
import uuid

from app.auth import Principal
from app.models.charging_session import ChargingSession
from app.models.ev import EV
from app.models.optimization_run import OptimizationRun
from app.services.driver.authorization import get_authorized_ev
from app.services.optimization.optimizer import get_active_run
from app.schemas.driver import (
    ScheduleAcceptRequest,
    ScheduleAcceptResponse,
    ScheduleOverrideRequest,
    ScheduleOverrideResponse,
)
from app.schemas.enums import OptimizationStatus, SessionStatus


def _get_or_create_session(db: Session, ev: EV) -> ChargingSession:
    session = db.query(ChargingSession).filter(ChargingSession.ev_id == ev.id).first()
    if session is None:
        session = ChargingSession(
            id=f"SESSION-{uuid.uuid4().hex[:8]}",
            ev_id=ev.id,
            charger_id=ev.charger_id,
            accepted=False,
            overridden=False,
            status=SessionStatus.pending.value,
        )
        db.add(session)
        db.flush()
    return session


def accept_schedule(
    db: Session, principal: Principal, req: ScheduleAcceptRequest, ev_id: str | None = None
) -> ScheduleAcceptResponse:
    ev = get_authorized_ev(db, principal, ev_id)

    run = db.get(OptimizationRun, req.optimization_run_id)
    if run is None:
        raise LookupError(f"Unknown optimization run {req.optimization_run_id}")
    if run.status != OptimizationStatus.applied.value:
        raise ValueError("Only the active optimization schedule can be accepted by a driver.")

    session = _get_or_create_session(db, ev)
    session.optimization_run_id = run.id
    session.accepted = True
    session.overridden = False
    session.status = SessionStatus.scheduled.value
    db.commit()
    db.refresh(session)

    return ScheduleAcceptResponse(ev_id=ev.id, accepted=True, status=SessionStatus.scheduled)


def override_schedule(
    db: Session, principal: Principal, req: ScheduleOverrideRequest, ev_id: str | None = None
) -> ScheduleOverrideResponse:
    ev = get_authorized_ev(db, principal, ev_id)

    feasible, explanation, alternatives = _check_feasibility(ev, req)
    session = _get_or_create_session(db, ev)
    active_run = get_active_run(db)
    if active_run is not None:
        session.optimization_run_id = active_run.id
    session.overridden = True
    session.accepted = False
    if feasible:
        session.status = SessionStatus.charging.value
    db.commit()
    db.refresh(session)

    return ScheduleOverrideResponse(
        ev_id=ev.id,
        overridden=True,
        status=SessionStatus(session.status),
        feasible=feasible,
        explanation=explanation,
        alternatives=alternatives,
    )


def _check_feasibility(ev: EV, req: ScheduleOverrideRequest) -> tuple[bool, str | None, list[str] | None]:
    if req.requested_power_kw is not None and req.requested_power_kw > ev.max_charge_kw:
        return (
            False,
            f"Charger for {ev.id} supports up to {ev.max_charge_kw} kW; {req.requested_power_kw} kW is not physically available.",
            [
                f"Charge at the maximum supported {ev.max_charge_kw} kW instead.",
                "Choose a different charger with higher rated power, if available.",
            ],
        )
    if req.requested_start_time is not None and not (
        ev.arrival_time <= req.requested_start_time <= ev.departure_time
    ):
        return (
            False,
            f"Requested start time is outside {ev.id}'s connection window ({ev.arrival_time} to {ev.departure_time}).",
            [
                "Choose a start time within your connection window.",
                "Charge at the assigned charger's supported power when available.",
            ],
        )
    return True, None, None