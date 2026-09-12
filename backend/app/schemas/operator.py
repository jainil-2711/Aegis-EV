"""Aegis charging-network operator API schemas (P4)."""

from pydantic import BaseModel

from app.schemas.enums import ChargerStatus, ConnectorType, GridCondition
from app.schemas.shared import BeforeAfter, EVLoad, PricingRule


class StationSummary(BaseModel):
    id: str
    name: str
    capacity_kw: float
    charger_count: int


class ChargerSummary(BaseModel):
    id: str
    station_id: str
    max_power_kw: float
    connector_type: ConnectorType
    status: ChargerStatus


class StationsResponse(BaseModel):
    stations: list[StationSummary]


class ChargersResponse(BaseModel):
    chargers: list[ChargerSummary]


class NetworkStatusResponse(BaseModel):
    active_evs: int
    active_chargers: int
    ev_load: EVLoad
    renewable_availability_pct: float
    grid_demand_kw: float
    grid_capacity_kw: float
    renewable_generation_kw: float


class NetworkImpactResponse(BaseModel):
    peak_load_kw: BeforeAfter
    cost: BeforeAfter
    renewable_share_pct: BeforeAfter
    co2_kg: BeforeAfter
    pricing_rule: PricingRule
    active_optimization_run_id: str
