"""GreenCharge Optimization API (P2)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models.charging_schedule_entry import ChargingScheduleEntry as ChargingScheduleEntryModel
from app.models.optimization_run import OptimizationRun
from app.schemas.enums import OptimizationStatus, OperatorObjective, Scenario
from app.schemas.optimization import (
    ChargingScheduleEntry,
    OptimizationApplyRequest,
    OptimizationApplyResponse,
    OptimizationMetrics,
    OptimizationRunDetailResponse,
    OptimizationRunRequest,
    OptimizationRunResponse,
    OptimizationScheduleResponse,
)
from app.services.optimization.optimizer import OptimizationError, OptimizationService, get_run_metrics

router = APIRouter(prefix="/api/optimization", tags=["optimization"])


def _to_schedule_schema(entry: ChargingScheduleEntryModel) -> ChargingScheduleEntry:
    return ChargingScheduleEntry(
        ev_id=entry.ev_id,
        timestamp=entry.timestamp,
        charging_power_kw=entry.charging_power_kw,
        energy_kwh=entry.energy_kwh,
        renewable_energy_kwh=entry.renewable_energy_kwh,
        grid_energy_kwh=entry.grid_energy_kwh,
        cost=entry.cost,
        co2_kg=entry.co2_kg,
    )


def _rebuild_run_response(
    db: Session,
    settings: Settings,
    run: OptimizationRun,
) -> OptimizationRunDetailResponse:
    entries = list(
        db.execute(
            select(ChargingScheduleEntryModel)
            .where(ChargingScheduleEntryModel.optimization_run_id == run.id)
            .order_by(
                ChargingScheduleEntryModel.timestamp.asc(),
                ChargingScheduleEntryModel.ev_id.asc(),
            )
        ).scalars().all()
    )
    baseline, candidate = get_run_metrics(db, settings, run)

    return OptimizationRunDetailResponse(
        id=run.id,
        status=OptimizationStatus(run.status),
        mode=OperatorObjective(run.mode),
        created_at=run.created_at,
        baseline=OptimizationMetrics(
            peak_kw=baseline.peak_kw,
            cost=baseline.cost,
            renewable_share_pct=baseline.renewable_share_pct,
            co2_kg=baseline.co2_kg,
        ),
        candidate=OptimizationMetrics(
            peak_kw=candidate.peak_kw,
            cost=candidate.cost,
            renewable_share_pct=candidate.renewable_share_pct,
            co2_kg=candidate.co2_kg,
        ),
        schedule=[_to_schedule_schema(e) for e in entries],
    )


def _peak_from_entries(entries: list[ChargingScheduleEntryModel]) -> float:
    by_ts: dict[datetime, float] = {}
    for entry in entries:
        by_ts[entry.timestamp] = by_ts.get(entry.timestamp, 0.0) + entry.charging_power_kw
    return max(by_ts.values(), default=0.0)


@router.post("/run", response_model=OptimizationRunResponse)
def run_optimization(
    payload: OptimizationRunRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OptimizationRunResponse:
    try:
        computation = OptimizationService(db, settings).run(
            mode=payload.mode,
            scenario=payload.scenario,
        )
    except OptimizationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    run = OptimizationRun(
        mode=payload.mode.value,
        baseline_peak_kw=computation.baseline.peak_kw,
        optimized_peak_kw=computation.candidate.peak_kw,
        baseline_cost=computation.baseline.cost,
        optimized_cost=computation.candidate.cost,
        status=OptimizationStatus.candidate.value,
    )
    db.add(run)
    db.flush()

    for point in computation.candidate_schedule:
        db.add(
            ChargingScheduleEntryModel(
                optimization_run_id=run.id,
                ev_id=point.ev_id,
                timestamp=point.timestamp,
                charging_power_kw=point.charging_power_kw,
                energy_kwh=point.energy_kwh,
                renewable_energy_kwh=point.renewable_energy_kwh,
                grid_energy_kwh=point.grid_energy_kwh,
                cost=point.cost,
                co2_kg=point.co2_kg,
            )
        )

    db.commit()
    db.refresh(run)

    return OptimizationRunResponse(
        id=run.id,
        status=OptimizationStatus.candidate,
        mode=payload.mode,
        created_at=run.created_at,
        baseline=OptimizationMetrics(
            peak_kw=computation.baseline.peak_kw,
            cost=computation.baseline.cost,
            renewable_share_pct=computation.baseline.renewable_share_pct,
            co2_kg=computation.baseline.co2_kg,
        ),
        candidate=OptimizationMetrics(
            peak_kw=computation.candidate.peak_kw,
            cost=computation.candidate.cost,
            renewable_share_pct=computation.candidate.renewable_share_pct,
            co2_kg=computation.candidate.co2_kg,
        ),
        schedule=[
            ChargingScheduleEntry(
                ev_id=p.ev_id,
                timestamp=p.timestamp,
                charging_power_kw=p.charging_power_kw,
                energy_kwh=p.energy_kwh,
                renewable_energy_kwh=p.renewable_energy_kwh,
                grid_energy_kwh=p.grid_energy_kwh,
                cost=p.cost,
                co2_kg=p.co2_kg,
            )
            for p in computation.candidate_schedule
        ],
    )


@router.post("/apply", response_model=OptimizationApplyResponse)
def apply_optimization(
    payload: OptimizationApplyRequest,
    db: Session = Depends(get_db),
) -> OptimizationApplyResponse:
    candidate = db.get(OptimizationRun, payload.optimization_run_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization run not found.")
    if candidate.status != OptimizationStatus.candidate.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a candidate optimization run can be applied.",
        )

    previous_applied = db.execute(
        select(OptimizationRun)
        .where(OptimizationRun.status == OptimizationStatus.applied.value)
        .order_by(OptimizationRun.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if previous_applied is not None:
        previous_applied.status = OptimizationStatus.superseded.value

    candidate.status = OptimizationStatus.applied.value
    db.commit()
    db.refresh(candidate)

    return OptimizationApplyResponse(
        id=candidate.id,
        status=OptimizationStatus.applied,
        applied_at=datetime.utcnow(),
        superseded_run_id=previous_applied.id if previous_applied else None,
    )


@router.get("/schedule", response_model=OptimizationScheduleResponse)
def get_active_schedule(db: Session = Depends(get_db)) -> OptimizationScheduleResponse:
    active = db.execute(
        select(OptimizationRun)
        .where(OptimizationRun.status == OptimizationStatus.applied.value)
        .order_by(OptimizationRun.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if active is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active optimization schedule.")

    entries = db.execute(
        select(ChargingScheduleEntryModel)
        .where(ChargingScheduleEntryModel.optimization_run_id == active.id)
        .order_by(ChargingScheduleEntryModel.timestamp.asc(), ChargingScheduleEntryModel.ev_id.asc())
    ).scalars().all()

    return OptimizationScheduleResponse(
        optimization_run_id=active.id,
        status=OptimizationStatus.applied,
        entries=[_to_schedule_schema(e) for e in entries],
    )


@router.get("/{optimization_id}", response_model=OptimizationRunDetailResponse)
def get_optimization_run(
    optimization_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OptimizationRunDetailResponse:
    run = db.get(OptimizationRun, optimization_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization run not found.")
    try:
        return _rebuild_run_response(db, settings, run)
    except OptimizationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
