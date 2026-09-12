"""
Aegis — Grid schemas (api-contract.md SS3, data-spec.md SS8)

Domain: P1. Shape is part of the frozen contract — mirrors api.ts.
"""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.enums import GridCondition, RenewableAvailability, SignalOperator
from app.schemas.shared import EnergySlot, EVLoad


class GridStatusResponse(BaseModel):
    grid_demand_kw: float
    grid_capacity_kw: float
    renewable_generation_kw: float
    ev_load: EVLoad
    headroom_kw: float


class GridForecastResponse(BaseModel):
    slots: list[EnergySlot]


class GridSignalCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    condition: GridCondition
    recommended_ev_load_kw: float
    signal_operator: SignalOperator
    renewable_availability: RenewableAvailability


class GridSignal(GridSignalCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GridSignalsResponse(BaseModel):
    signals: list[GridSignal]


class GridEVLoadResponse(BaseModel):
    ev_load: EVLoad
