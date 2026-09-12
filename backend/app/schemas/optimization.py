"""
Aegis — Optimization API schemas (P2).

These shapes mirror the frozen optimization section of the shared API contract
and the canonical schemas.py supplied with the hackathon package.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import OptimizationStatus, OperatorObjective, Scenario


class OptimizationRunRequest(BaseModel):
    mode: OperatorObjective
    scenario: Optional[Scenario] = None


class ChargingScheduleEntry(BaseModel):
    ev_id: str
    timestamp: datetime
    charging_power_kw: float
    energy_kwh: float
    renewable_energy_kwh: float
    grid_energy_kwh: float
    cost: float
    co2_kg: float


class OptimizationMetrics(BaseModel):
    peak_kw: float
    cost: float
    renewable_share_pct: float
    co2_kg: float


class OptimizationRunResponse(BaseModel):
    """Baseline and candidate are produced together by one optimizer run."""

    id: str
    status: OptimizationStatus
    mode: OperatorObjective
    created_at: datetime
    baseline: OptimizationMetrics
    candidate: OptimizationMetrics
    schedule: list[ChargingScheduleEntry]


class OptimizationApplyRequest(BaseModel):
    optimization_run_id: str


class OptimizationApplyResponse(BaseModel):
    id: str
    status: OptimizationStatus
    applied_at: datetime
    superseded_run_id: str | None = None


class OptimizationRunDetailResponse(OptimizationRunResponse):
    pass


class OptimizationScheduleResponse(BaseModel):
    optimization_run_id: str
    status: OptimizationStatus
    entries: list[ChargingScheduleEntry]
