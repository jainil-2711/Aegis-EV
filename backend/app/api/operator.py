"""
GreenCharge — Operator API Router (P4)

Endpoints (api-contract.md SS4, SS5):
    GET /api/stations
    GET /api/chargers
    GET /api/network/status
    GET /api/network/impact

This file only wires HTTP <-> services. No business logic here.
Optimization run/apply are P2-owned (POST /api/optimization/run,
POST /api/optimization/apply) — this router does not duplicate them;
the frontend calls P2's optimization client directly.

Registration (main.py, append-only one line):
    from app.api.operator import router as operator_router
    app.include_router(operator_router, prefix="/api", tags=["operator"])
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db

from app.services.operator.stations import get_stations
from app.services.operator.chargers import get_chargers
from app.services.operator.network import (
    get_network_status,
    get_network_impact,
    NoActiveScheduleError,
)

from app.schemas.operator import (
    StationsResponse,
    ChargersResponse,
    NetworkStatusResponse,
    NetworkImpactResponse,
)

router = APIRouter()


@router.get("/stations", response_model=StationsResponse)
def read_stations(db: Session = Depends(get_db)):
    return get_stations(db)


@router.get("/chargers", response_model=ChargersResponse)
def read_chargers(
    station_id: str | None = Query(default=None), db: Session = Depends(get_db)
):
    return get_chargers(db, station_id=station_id)


@router.get("/network/status", response_model=NetworkStatusResponse)
def read_network_status(db: Session = Depends(get_db)):
    return get_network_status(db)


@router.get("/network/impact", response_model=NetworkImpactResponse)
def read_network_impact(db: Session = Depends(get_db)):
    try:
        return get_network_impact(db)
    except NoActiveScheduleError as exc:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "NO_ACTIVE_SCHEDULE", "message": str(exc)}},
        )
