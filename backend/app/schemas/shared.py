"""
Aegis — Shared value-object schemas (SHARED, frozen contract)

Mirrors api.ts field-for-field (rules.md SS12).
"""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.enums import GridCondition


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class EVLoad(BaseModel):
    """Returned identically by /api/grid/status and /api/network/status.
    Both MUST source these three fields from services/shared/ev_load.py
    (architecture.md SS4) — never computed independently."""

    current_ev_load_kw: float
    scheduled_ev_load_kw: float
    peak_ev_load_kw: float


class EnergySlot(BaseModel):
    timestamp: datetime
    base_load_kw: float
    renewable_kw: float
    grid_capacity_kw: float
    electricity_price: float
    carbon_intensity: float

    model_config = {"from_attributes": True}


class PricingTier(BaseModel):
    condition: GridCondition
    price_per_kwh: float


class PricingRule(BaseModel):
    """Returned inside /api/network/impact — see api-contract.md SS8.
    No dedicated pricing endpoint."""

    base_rate: float
    currency: str = "INR"
    tiers: list[PricingTier]


class BeforeAfter(BaseModel):
    before: float
    after: float
