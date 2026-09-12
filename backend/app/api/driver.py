"""Driver API routes (P3).

Every route resolves its EV through the authenticated principal
(see app.services.driver.authorization.get_authorized_ev). An optional
`ev_id` query param is still accepted for forward-compatibility with
multi-vehicle drivers, but it is only ever used to *confirm* a match against
the EV bound to this driver's account — never to look up an arbitrary EV.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import Principal, ROLE_DRIVER, require_role
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.driver import (
    DriverPreferencesUpdate,
    DriverRecommendationResponse,
    DriverSessionResponse,
    DriverSessionStatusResponse,
    ScheduleAcceptRequest,
    ScheduleAcceptResponse,
    ScheduleOverrideRequest,
    ScheduleOverrideResponse,
)
from app.services.driver.authorization import EVAccessDeniedError
from app.services.driver.recommendation import NoActiveScheduleError, get_driver_recommendation
from app.services.driver.schedule import accept_schedule, override_schedule
from app.services.driver.session import get_driver_session, update_driver_preferences
from app.services.driver.status import get_session_status

router = APIRouter()

EvIdQuery = Query(default=None, description="Must match the EV bound to this driver's account.")


def _forbidden(exc: EVAccessDeniedError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"error": {"code": "EV_NOT_AUTHORIZED", "message": str(exc)}},
    )


def _no_ev_assigned(exc: LookupError) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"error": {"code": "NO_EV_ASSIGNED", "message": str(exc)}},
    )


@router.get("/session", response_model=DriverSessionResponse)
def read_driver_session(
    ev_id: str | None = EvIdQuery,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role(ROLE_DRIVER)),
):
    try:
        return get_driver_session(db, principal, ev_id)
    except EVAccessDeniedError as exc:
        raise _forbidden(exc) from exc
    except LookupError as exc:
        raise _no_ev_assigned(exc) from exc


@router.post("/preferences", response_model=DriverSessionResponse)
def update_preferences(
    update: DriverPreferencesUpdate,
    ev_id: str | None = EvIdQuery,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role(ROLE_DRIVER)),
):
    try:
        return update_driver_preferences(db, principal, update, ev_id)
    except EVAccessDeniedError as exc:
        raise _forbidden(exc) from exc
    except LookupError as exc:
        raise _no_ev_assigned(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_PREFERENCES", "message": str(exc)}}) from exc


@router.get("/recommendation", response_model=DriverRecommendationResponse)
def read_driver_recommendation(
    ev_id: str | None = EvIdQuery,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role(ROLE_DRIVER)),
):
    try:
        return get_driver_recommendation(db, principal, ev_id)
    except EVAccessDeniedError as exc:
        raise _forbidden(exc) from exc
    except LookupError as exc:
        raise _no_ev_assigned(exc) from exc
    except NoActiveScheduleError as exc:
        message = str(exc)
        code = "NO_ACTIVE_SCHEDULE" if "No active optimization schedule" in message else "NO_SCHEDULE_ENTRIES"
        raise HTTPException(status_code=409, detail={"error": {"code": code, "message": message}}) from exc


@router.post("/schedule/accept", response_model=ScheduleAcceptResponse)
def accept_recommendation(
    req: ScheduleAcceptRequest,
    ev_id: str | None = EvIdQuery,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role(ROLE_DRIVER)),
):
    try:
        return accept_schedule(db, principal, req, ev_id)
    except EVAccessDeniedError as exc:
        raise _forbidden(exc) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(exc)}}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"error": {"code": "INVALID_SESSION_ACTION", "message": str(exc)}}) from exc


@router.post("/schedule/override", response_model=ScheduleOverrideResponse)
def override_recommendation(
    req: ScheduleOverrideRequest,
    ev_id: str | None = EvIdQuery,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role(ROLE_DRIVER)),
):
    try:
        return override_schedule(db, principal, req, ev_id)
    except EVAccessDeniedError as exc:
        raise _forbidden(exc) from exc
    except LookupError as exc:
        raise _no_ev_assigned(exc) from exc


@router.get("/session/status", response_model=DriverSessionStatusResponse)
def read_session_status(
    ev_id: str | None = EvIdQuery,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role(ROLE_DRIVER)),
):
    try:
        return get_session_status(db, principal, ev_id)
    except EVAccessDeniedError as exc:
        raise _forbidden(exc) from exc
    except LookupError as exc:
        raise _no_ev_assigned(exc) from exc