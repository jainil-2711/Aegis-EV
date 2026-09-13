"""Deterministic simulated-live driver status service (P3)."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Principal
from app.config import get_settings
from app.models.charging_schedule_entry import ChargingScheduleEntry
from app.models.charging_session import ChargingSession
from app.models.ev import EV
from app.models.energy_slot import EnergySlot
from app.engine.green_score import calculate_green_score
from app.schemas.driver import DriverSessionStatusResponse
from app.schemas.enums import SessionStatus
from app.services.driver.authorization import get_authorized_ev
from app.services.optimization.optimizer import get_active_run
from app.services.shared.simulation_clock import current_demo_timestamp


def get_session_status(
    db: Session, principal: Principal, ev_id: str | None = None
) -> DriverSessionStatusResponse:
    ev = get_authorized_ev(db, principal, ev_id)
    ev_id = ev.id

    session = (
        db.query(ChargingSession)
        .filter(ChargingSession.ev_id == ev_id)
        .first()
    )

    status = SessionStatus(session.status) if session else SessionStatus.pending

    now = current_demo_timestamp(get_settings())

    # ------------------------------------------------------------------
    # DRIVER OVERRIDE PATH
    # ------------------------------------------------------------------
    # An override is deliberately kept separate from the published
    # optimization schedule. The driver can charge now without changing
    # the operator's published candidate/active schedule.
    if (
        session is not None
        and session.overridden
        and session.status == SessionStatus.charging.value
        and session.override_power_kw is not None
        and session.override_started_at is not None
    ):
        power_kw = min(
            session.override_power_kw,
            ev.max_charge_kw,
        )

        # The override can only simulate while the EV is physically
        # connected.
        start_time = max(
            session.override_started_at,
            ev.arrival_time,
        )
        end_time = min(
            now,
            ev.departure_time,
        )

        elapsed_hours = max(
            0.0,
            (end_time - start_time).total_seconds() / 3600.0,
        )

        energy_so_far = power_kw * elapsed_hours

        renewable_so_far = 0.0
        cost_so_far = 0.0
        co2_so_far = 0.0

        # Walk through overlapping energy slots so cost, renewable
        # attribution and CO2 use the same underlying grid data model
        # as the normal optimization path.
        slots = list(
            db.execute(
                select(EnergySlot)
                .where(
                    EnergySlot.timestamp <= end_time,
                    EnergySlot.timestamp >= ev.arrival_time,
                )
                .order_by(EnergySlot.timestamp.asc())
            )
            .scalars()
            .all()
        )

        remaining_energy = energy_so_far

        for slot in slots:
            slot_start = slot.timestamp
            slot_end = slot_start + timedelta(minutes=30)

            overlap_start = max(start_time, slot_start)
            overlap_end = min(end_time, slot_end)

            if overlap_end <= overlap_start:
                continue

            overlap_hours = (
                overlap_end - overlap_start
            ).total_seconds() / 3600.0

            slot_energy = min(
                remaining_energy,
                power_kw * overlap_hours,
            )

            if slot_energy <= 0:
                continue

            renewable_available = max(
                0.0,
                slot.renewable_kw,
            ) * overlap_hours

            renewable_energy = min(
                slot_energy,
                renewable_available,
            )

            grid_energy = max(
                0.0,
                slot_energy - renewable_energy,
            )

            renewable_so_far += renewable_energy
            cost_so_far += slot_energy * slot.electricity_price
            co2_so_far += grid_energy * slot.carbon_intensity

            remaining_energy -= slot_energy

            if remaining_energy <= 0:
                break

        if energy_so_far > 0:
            renewable_share_pct = (
                renewable_so_far / energy_so_far
            ) * 100.0

            grid_share_pct = max(
                0.0,
                100.0 - renewable_share_pct,
            )

            grid_energy_so_far = max(
                0.0,
                energy_so_far - renewable_so_far,
            )

            average_carbon = (
                co2_so_far / energy_so_far
                if energy_so_far > 0
                else 0.0
            )

            green_score = calculate_green_score(
                renewable_share_pct=renewable_share_pct,
                average_carbon_intensity=average_carbon,
                grid_energy_kwh=grid_energy_so_far,
                total_energy_kwh=energy_so_far,
            )
        else:
            renewable_share_pct = 0.0
            grid_share_pct = 0.0
            green_score = None

        current_soc = _project_soc(
            ev,
            energy_so_far,
        )

        return DriverSessionStatusResponse(
            status=SessionStatus.charging,
            current_soc=round(current_soc, 1),
            charging_power_kw=round(power_kw, 2),
            renewable_share_pct=round(renewable_share_pct, 1),
            grid_share_pct=round(grid_share_pct, 1),
            cost_so_far=round(cost_so_far, 2),
            co2_kg_so_far=round(co2_so_far, 2),
            green_score=green_score,
            simulated=True,
            updated_at=now,
        )

    # ------------------------------------------------------------------
    # NORMAL PUBLISHED-SCHEDULE PATH
    # ------------------------------------------------------------------
    run = get_active_run(db)

    entries: list[ChargingScheduleEntry] = []

    if run is not None:
        entries = list(
            db.execute(
                select(ChargingScheduleEntry)
                .where(
                    ChargingScheduleEntry.optimization_run_id == run.id,
                    ChargingScheduleEntry.ev_id == ev_id,
                    ChargingScheduleEntry.charging_power_kw > 0,
                )
                .order_by(ChargingScheduleEntry.timestamp.asc())
            )
            .scalars()
            .all()
        )

    elapsed = [
        entry
        for entry in entries
        if entry.timestamp <= now
    ]

    energy_so_far = sum(
        e.energy_kwh for e in elapsed
    )
    renewable_so_far = sum(
        e.renewable_energy_kwh for e in elapsed
    )
    cost_so_far = sum(
        e.cost for e in elapsed
    )
    co2_so_far = sum(
        e.co2_kg for e in elapsed
    )

    current_entry = elapsed[-1] if elapsed else None

    charging_power_kw = (
        current_entry.charging_power_kw
        if current_entry
        else 0.0
    )

    renewable_share_pct = (
        renewable_so_far / energy_so_far * 100.0
        if energy_so_far
        else 0.0
    )

    grid_share_pct = (
        max(
            0.0,
            100.0 - renewable_share_pct,
        )
        if energy_so_far
        else 0.0
    )

    current_soc = _project_soc(
        ev,
        energy_so_far,
    )

    if elapsed and energy_so_far > 0:
        slot_map = {
            row.timestamp: row
            for row in db.execute(
                select(EnergySlot).where(
                    EnergySlot.timestamp.in_(
                        [e.timestamp for e in elapsed]
                    )
                )
            )
            .scalars()
            .all()
        }

        weighted_carbon = sum(
            e.grid_energy_kwh
            * slot_map[e.timestamp].carbon_intensity
            for e in elapsed
            if e.timestamp in slot_map
        )

        avg_carbon = (
            weighted_carbon / energy_so_far
        )

        green_score = calculate_green_score(
            renewable_share_pct=renewable_share_pct,
            average_carbon_intensity=avg_carbon,
            grid_energy_kwh=sum(
                e.grid_energy_kwh
                for e in elapsed
            ),
            total_energy_kwh=energy_so_far,
        )

    elif entries:
        total_energy = sum(
            e.energy_kwh for e in entries
        )
        total_renewable = sum(
            e.renewable_energy_kwh for e in entries
        )
        total_grid = sum(
            e.grid_energy_kwh for e in entries
        )

        slot_map = {
            row.timestamp: row
            for row in db.execute(
                select(EnergySlot).where(
                    EnergySlot.timestamp.in_(
                        [e.timestamp for e in entries]
                    )
                )
            )
            .scalars()
            .all()
        }

        weighted_carbon = sum(
            e.grid_energy_kwh
            * slot_map[e.timestamp].carbon_intensity
            for e in entries
            if e.timestamp in slot_map
        )

        avg_carbon = (
            weighted_carbon / total_energy
            if total_energy
            else 0.0
        )

        green_score = calculate_green_score(
            renewable_share_pct=(
                total_renewable / total_energy * 100.0
                if total_energy
                else 0.0
            ),
            average_carbon_intensity=avg_carbon,
            grid_energy_kwh=total_grid,
            total_energy_kwh=total_energy,
        )

    else:
        green_score = None

    if (
        entries
        and len(elapsed) == len(entries)
        and elapsed
    ):
        status = SessionStatus.completed

    elif (
        elapsed
        and status == SessionStatus.scheduled
    ):
        status = SessionStatus.charging

    return DriverSessionStatusResponse(
        status=status,
        current_soc=round(current_soc, 1),
        charging_power_kw=round(
            charging_power_kw,
            2,
        ),
        renewable_share_pct=round(
            renewable_share_pct,
            1,
        ),
        grid_share_pct=round(
            grid_share_pct,
            1,
        ),
        cost_so_far=round(
            cost_so_far,
            2,
        ),
        co2_kg_so_far=round(
            co2_so_far,
            2,
        ),
        green_score=green_score,
        simulated=True,
        updated_at=now,
    )


def _project_soc(
    ev: EV,
    energy_delivered_kwh: float,
) -> float:
    soc_gain_pct = (
        energy_delivered_kwh
        * ev.efficiency
        / ev.battery_capacity_kwh
        * 100.0
        if ev.battery_capacity_kwh > 0
        else 0.0
    )

    return min(
        ev.current_soc + soc_gain_pct,
        ev.target_soc,
    )
