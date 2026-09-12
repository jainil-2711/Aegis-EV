"""
GreenCharge — Grid API (P1) — api-contract.md SS3

Routes:
    GET  /api/grid/status
    GET  /api/grid/forecast
    POST /api/grid/signals
    GET  /api/grid/signals
    GET  /api/grid/ev-load
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.schemas.grid import (
    GridEVLoadResponse,
    GridForecastResponse,
    GridSignal,
    GridSignalCreate,
    GridSignalsResponse,
    GridStatusResponse,
)
from app.schemas.shared import EnergySlot as EnergySlotSchema
from app.schemas.shared import EVLoad
from app.services.grid.signals import create_signal, list_signals
from app.services.grid.status import build_grid_status, list_forecast_slots
from app.services.shared.ev_load import get_ev_load

router = APIRouter(prefix="/api/grid", tags=["grid"])


@router.get("/status", response_model=GridStatusResponse)
def get_grid_status(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> GridStatusResponse:
    return build_grid_status(db, settings)


@router.get("/forecast", response_model=GridForecastResponse)
def get_grid_forecast(db: Session = Depends(get_db)) -> GridForecastResponse:
    slots = list_forecast_slots(db)
    return GridForecastResponse(
        slots=[EnergySlotSchema.model_validate(s) for s in slots]
    )


@router.post("/signals", response_model=GridSignal, status_code=201)
def post_grid_signal(
    payload: GridSignalCreate, db: Session = Depends(get_db)
) -> GridSignal:
    signal = create_signal(db, payload)
    return GridSignal.model_validate(signal)


@router.get("/signals", response_model=GridSignalsResponse)
def get_grid_signals(db: Session = Depends(get_db)) -> GridSignalsResponse:
    signals = list_signals(db)
    return GridSignalsResponse(signals=[GridSignal.model_validate(s) for s in signals])


@router.get("/ev-load", response_model=GridEVLoadResponse)
def get_grid_ev_load(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> GridEVLoadResponse:
    result = get_ev_load(db, settings)
    return GridEVLoadResponse(
        ev_load=EVLoad(
            current_ev_load_kw=result.current_ev_load_kw,
            scheduled_ev_load_kw=result.scheduled_ev_load_kw,
            peak_ev_load_kw=result.peak_ev_load_kw,
        )
    )
