"""Aegis driver API schemas (P3).

Shapes follow the Driver section of the project API contract. Green Score is
computed by the backend's deterministic environmental accounting layer.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.enums import DriverPreference, Flexibility, SessionStatus


class DriverSessionResponse(BaseModel):
    ev_id: str
    battery_capacity_kwh: float
    current_soc: float
    target_soc: float
    arrival_time: datetime
    departure_time: datetime
    max_charge_kw: float
    efficiency: float
    preference: DriverPreference
    charger_id: str
    flexibility: Flexibility


class DriverPreferencesUpdate(BaseModel):
    preference: DriverPreference
    target_soc: Optional[float] = Field(default=None, ge=0, le=100)
    departure_time: Optional[datetime] = None


class DriverRecommendationResponse(BaseModel):
    optimization_run_id: str
    window_start: datetime
    window_end: datetime
    estimated_cost: float
    price_per_kwh: float
    renewable_share_pct: float
    co2_impact_kg: float
    green_score: Optional[float] = None
    why: str


class ScheduleAcceptRequest(BaseModel):
    optimization_run_id: str


class ScheduleAcceptResponse(BaseModel):
    ev_id: str
    accepted: bool
    status: SessionStatus


class ScheduleOverrideRequest(BaseModel):
    requested_power_kw: Optional[float] = Field(default=None, gt=0)
    requested_start_time: Optional[datetime] = None
    reason: Optional[str] = None


class ScheduleOverrideResponse(BaseModel):
    ev_id: str
    overridden: bool
    status: SessionStatus
    feasible: bool
    explanation: Optional[str] = None
    alternatives: Optional[list[str]] = None


class DriverSessionStatusResponse(BaseModel):
    status: SessionStatus
    current_soc: float
    charging_power_kw: float
    renewable_share_pct: float
    grid_share_pct: float
    cost_so_far: float
    co2_kg_so_far: float
    green_score: Optional[float] = None
    simulated: bool
    updated_at: datetime
