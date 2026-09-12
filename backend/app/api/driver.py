"""Driver API routes (P3)."""

from fastapi import APIRouter, Depends, HTTPException, status

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
from app.services.driver.recommendation import NoActiveScheduleError, get_driver_recommendation
from app.services.driver.schedule import accept_schedule, override_schedule
from app.services.driver.session import DEMO_EV_ID, get_driver_session, update_driver_preferences
from app.services.driver.status import get_session_status

router = APIRouter()


@router.get("/session", response_model=DriverSessionResponse)
def read_driver_session(db: Session = Depends(get_db), _: Principal = Depends(require_role(ROLE_DRIVER))):
    try:
        return get_driver_session(db)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "NO_SEEDED_EV", "message": str(exc)}}) from exc


@router.post("/preferences", response_model=DriverSessionResponse)
def update_preferences(update: DriverPreferencesUpdate, db: Session = Depends(get_db), _: Principal = Depends(require_role(ROLE_DRIVER))):
    try:
        return update_driver_preferences(db, update)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "NO_SEEDED_EV", "message": str(exc)}}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_PREFERENCES", "message": str(exc)}}) from exc


@router.get("/recommendation", response_model=DriverRecommendationResponse)
def read_driver_recommendation(ev_id: str = DEMO_EV_ID, db: Session = Depends(get_db), _: Principal = Depends(require_role(ROLE_DRIVER))):
    try:
        return get_driver_recommendation(db, ev_id)
    except NoActiveScheduleError as exc:
        message = str(exc)
        code = "NO_ACTIVE_SCHEDULE" if "No active optimization schedule" in message else "UNKNOWN_EV"
        raise HTTPException(status_code=409 if code == "NO_ACTIVE_SCHEDULE" else 404, detail={"error": {"code": code, "message": message}}) from exc


@router.post("/schedule/accept", response_model=ScheduleAcceptResponse)
def accept_recommendation(
    req: ScheduleAcceptRequest,
    ev_id: str = DEMO_EV_ID,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_role(ROLE_DRIVER)),
):
    try:
        return accept_schedule(db, ev_id, req)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(exc)}}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"error": {"code": "INVALID_SESSION_ACTION", "message": str(exc)}}) from exc


@router.post("/schedule/override", response_model=ScheduleOverrideResponse)
def override_recommendation(
    req: ScheduleOverrideRequest,
    ev_id: str = DEMO_EV_ID,
    db: Session = Depends(get_db),
    _: Principal = Depends(require_role(ROLE_DRIVER)),
):
    try:
        return override_schedule(db, ev_id, req)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "UNKNOWN_EV", "message": str(exc)}}) from exc


@router.get("/session/status", response_model=DriverSessionStatusResponse)
def read_session_status(ev_id: str = DEMO_EV_ID, db: Session = Depends(get_db), _: Principal = Depends(require_role(ROLE_DRIVER))):
    try:
        return get_session_status(db, ev_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "UNKNOWN_EV", "message": str(exc)}}) from exc
