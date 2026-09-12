"""
Aegis — Grid API schemas (P1)

These schemas define the Grid API contract.

Grid numerical relationships:

    renewable_generation_kw
        = solar_generation_kw + wind_generation_kw

    grid_demand_kw
        = base_load_kw + current_ev_load_kw

    headroom_kw
        = grid_capacity_kw - grid_demand_kw
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.enums import (
    GridCondition,
    RenewableAvailability,
    SignalOperator,
)
from app.schemas.shared import EnergySlot, EVLoad


class GridStatusResponse(BaseModel):
    """Current grid/network state for the active demo timestamp."""

    # Grid demand components
    base_load_kw: float = Field(
        ge=0.0,
    )

    ev_load: EVLoad

    grid_demand_kw: float

    # Grid capacity/headroom
    grid_capacity_kw: float
    headroom_kw: float

    # Renewable generation
    solar_generation_kw: float = Field(
        ge=0.0,
    )

    wind_generation_kw: float = Field(
        ge=0.0,
    )

    renewable_generation_kw: float = Field(
        ge=0.0,
    )

    # Data provenance
    source_type: str


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

    model_config = {
        "from_attributes": True
    }


class GridSignalsResponse(BaseModel):
    signals: list[GridSignal]


class GridEVLoadResponse(BaseModel):
    ev_load: EVLoad