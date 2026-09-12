"""
GreenCharge — canonical optimization service (P2).

The service owns the deterministic optimization implementation described in
architecture.md / phases.md. OR-Tools CP-SAT is the canonical solver.

Phase 1–3 responsibilities implemented here:
- canonical optimizer interface: run(db, mode, scenario)
- deterministic feasible baseline: charge as early as possible at maximum
  feasible power within each EV's window
- hard physical constraints
- operator objectives: cheapest / greenest / balanced
- driver preference as a soft signal
- flexibility-aware shifting
- GridSignal as a soft objective signal (never a hard constraint)
- candidate schedule generation and metrics

Pricing, carbon/Green Score engines, scenarios, explanations, and driver-facing
APIs are deliberately kept out of this module until their planned phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.charger import Charger
from app.models.charging_schedule_entry import ChargingScheduleEntry
from app.models.energy_slot import EnergySlot
from app.models.ev import EV
from app.models.grid_signal import GridSignal
from app.models.optimization_run import OptimizationRun
from app.models.station import Station
from app.schemas.enums import OperatorObjective, Scenario

try:  # Lazy availability guard; importing the app should stay informative.
    from ortools.sat.python import cp_model
except ImportError:  # pragma: no cover - environment dependent
    cp_model = None


SLOT_MINUTES = 30
POWER_UNIT_KW = 0.1
ENERGY_UNIT_KWH = 0.01


class OptimizationError(RuntimeError):
    """Expected optimizer failure that can be presented to the API client."""


@dataclass(frozen=True)
class SlotContext:
    timestamp: datetime
    base_load_kw: float
    renewable_kw: float
    grid_capacity_kw: float
    electricity_price: float
    carbon_intensity: float


@dataclass(frozen=True)
class EVContext:
    ev: EV
    charger: Charger
    station: Station
    required_energy_kwh: float


@dataclass(frozen=True)
class SchedulePoint:
    ev_id: str
    timestamp: datetime
    charging_power_kw: float
    energy_kwh: float
    renewable_energy_kwh: float
    grid_energy_kwh: float
    cost: float
    co2_kg: float


@dataclass(frozen=True)
class Metrics:
    peak_kw: float
    cost: float
    renewable_share_pct: float
    co2_kg: float


@dataclass(frozen=True)
class OptimizationComputation:
    baseline: Metrics
    candidate: Metrics
    baseline_schedule: list[SchedulePoint]
    candidate_schedule: list[SchedulePoint]


def get_active_run(db: Session) -> OptimizationRun | None:
    """Return the canonical active optimization run, if one exists.

    This read-only integration surface is owned by P2 so other role modules
    do not duplicate optimization-state queries.
    """
    return db.execute(
        select(OptimizationRun)
        .where(OptimizationRun.status == "applied")
        .order_by(OptimizationRun.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def get_active_or_latest_run(db: Session) -> OptimizationRun | None:
    """Return active run, otherwise the most recent candidate run."""
    active = get_active_run(db)
    if active is not None:
        return active
    return db.execute(
        select(OptimizationRun)
        .where(OptimizationRun.status == "candidate")
        .order_by(OptimizationRun.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def get_run_metrics(
    db: Session, settings: Settings, run: OptimizationRun
) -> tuple[Metrics, Metrics]:
    """Return the canonical baseline and candidate metrics for a stored run.

    This is a read-only P2 integration surface for other role modules. It
    centralizes metric reconstruction so driver/operator views do not compute
    optimization impact independently.
    """
    entries = list(
        db.execute(
            select(ChargingScheduleEntry)
            .where(ChargingScheduleEntry.optimization_run_id == run.id)
            .order_by(ChargingScheduleEntry.timestamp.asc(), ChargingScheduleEntry.ev_id.asc())
        ).scalars().all()
    )

    candidate_cost = round(sum(e.cost for e in entries), 2)
    total_energy = sum(e.energy_kwh for e in entries)
    renewable_energy = sum(e.renewable_energy_kwh for e in entries)
    candidate_co2 = round(sum(e.co2_kg for e in entries), 2)
    candidate_share = round(
        (renewable_energy / total_energy * 100.0) if total_energy else 0.0, 2
    )
    by_timestamp: dict[datetime, float] = {}
    for entry in entries:
        by_timestamp[entry.timestamp] = (
            by_timestamp.get(entry.timestamp, 0.0) + entry.charging_power_kw
        )
    candidate_peak = round(max(by_timestamp.values(), default=0.0), 2)

    baseline = OptimizationService(
        db, settings
    ).run(
        mode=OperatorObjective(run.mode),
        scenario=None,
    ).baseline

    candidate = Metrics(
        peak_kw=candidate_peak,
        cost=candidate_cost,
        renewable_share_pct=candidate_share,
        co2_kg=candidate_co2,
    )
    return baseline, candidate


class OptimizationService:
    """Deterministic OR-Tools implementation for GreenCharge."""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings

    def run(
        self,
        mode: OperatorObjective,
        scenario: Scenario | None = None,
    ) -> OptimizationComputation:
        if cp_model is None:
            raise OptimizationError(
                "OR-Tools is required for GreenCharge optimization. "
                "Install dependencies with `pip install -r backend/requirements.txt`."
            )

        if scenario not in (None, Scenario.normal):
            raise OptimizationError(
                "Non-normal scenarios are reserved for Phase 12. "
                "Use scenario='normal' or omit scenario for the current optimizer."
            )

        slots = self._load_slots()
        evs = self._load_evs()
        chargers = self._load_chargers()
        stations = self._load_stations()
        signals = self._load_signals()

        if not slots:
            raise OptimizationError("No EnergySlot data is available. Run scripts/seed_demo.py first.")
        if not evs:
            raise OptimizationError("No EV data is available. Run scripts/seed_demo.py first.")

        contexts = self._build_ev_contexts(evs, chargers, stations)
        slot_contexts = [
            SlotContext(
                timestamp=s.timestamp,
                base_load_kw=s.base_load_kw,
                renewable_kw=s.renewable_kw,
                grid_capacity_kw=s.grid_capacity_kw,
                electricity_price=s.electricity_price,
                carbon_intensity=s.carbon_intensity,
            )
            for s in slots
        ]

        baseline_power = self._solve_power_matrix(
            ev_contexts=contexts,
            slots=slot_contexts,
            signals=signals,
            objective=mode,
            baseline=True,
        )
        candidate_power = self._solve_power_matrix(
            ev_contexts=contexts,
            slots=slot_contexts,
            signals=signals,
            objective=mode,
            baseline=False,
        )

        baseline_schedule = self._matrix_to_schedule(contexts, slot_contexts, baseline_power)
        candidate_schedule = self._matrix_to_schedule(contexts, slot_contexts, candidate_power)

        return OptimizationComputation(
            baseline=self._metrics(baseline_schedule, slot_contexts),
            candidate=self._metrics(candidate_schedule, slot_contexts),
            baseline_schedule=baseline_schedule,
            candidate_schedule=candidate_schedule,
        )

    # ------------------------------------------------------------------
    # Data loading / validation
    # ------------------------------------------------------------------

    def _load_slots(self) -> list[EnergySlot]:
        return list(
            self.db.execute(select(EnergySlot).order_by(EnergySlot.timestamp.asc())).scalars().all()
        )

    def _load_evs(self) -> list[EV]:
        return list(self.db.execute(select(EV).order_by(EV.id.asc())).scalars().all())

    def _load_chargers(self) -> dict[str, Charger]:
        rows = self.db.execute(select(Charger)).scalars().all()
        return {row.id: row for row in rows}

    def _load_stations(self) -> dict[str, Station]:
        rows = self.db.execute(select(Station)).scalars().all()
        return {row.id: row for row in rows}

    def _load_signals(self) -> list[GridSignal]:
        return list(
            self.db.execute(select(GridSignal).order_by(GridSignal.created_at.asc())).scalars().all()
        )

    def _build_ev_contexts(
        self,
        evs: Iterable[EV],
        chargers: dict[str, Charger],
        stations: dict[str, Station],
    ) -> list[EVContext]:
        contexts: list[EVContext] = []
        for ev in evs:
            charger = chargers.get(ev.charger_id)
            if charger is None:
                raise OptimizationError(f"EV {ev.id} references missing charger {ev.charger_id}.")
            station = stations.get(charger.station_id)
            if station is None:
                raise OptimizationError(
                    f"Charger {charger.id} references missing station {charger.station_id}."
                )
            required = self._required_energy_kwh(ev)
            if required <= 0:
                continue
            if ev.departure_time <= ev.arrival_time:
                raise OptimizationError(f"EV {ev.id} has an invalid charging window.")
            contexts.append(EVContext(ev=ev, charger=charger, station=station, required_energy_kwh=required))
        return contexts

    @staticmethod
    def _required_energy_kwh(ev: EV) -> float:
        # Authoritative formula from data-spec.md: battery energy needed for
        # the SOC increase, adjusted for charging efficiency.
        return max(
            0.0,
            ev.battery_capacity_kwh * (ev.target_soc - ev.current_soc) / 100.0 / ev.efficiency,
        )

    # ------------------------------------------------------------------
    # CP-SAT model
    # ------------------------------------------------------------------

    def _solve_power_matrix(
        self,
        *,
        ev_contexts: list[EVContext],
        slots: list[SlotContext],
        signals: list[GridSignal],
        objective: OperatorObjective,
        baseline: bool,
    ) -> dict[tuple[str, int], int]:
        assert cp_model is not None
        model = cp_model.CpModel()

        vars_by_key: dict[tuple[str, int], cp_model.IntVar] = {}
        slot_total: list[cp_model.IntVar] = []

        # Index the relevant variables per charger/station.
        charger_vars: dict[tuple[str, int], list[cp_model.IntVar]] = {}
        station_vars: dict[tuple[str, int], list[cp_model.IntVar]] = {}

        for evc in ev_contexts:
            ev = evc.ev
            max_units = max(
                0,
                int(math.floor(min(ev.max_charge_kw, evc.charger.max_power_kw) / POWER_UNIT_KW + 1e-9)),
            )
            if max_units <= 0:
                raise OptimizationError(f"EV {ev.id} has no usable charging power.")

            available_variable_count = 0
            for i, slot in enumerate(slots):
                overlap_hours = self._slot_overlap_hours(slot.timestamp, ev.arrival_time, ev.departure_time)
                if overlap_hours <= 0:
                    continue

                var = model.NewIntVar(0, max_units, f"p_{ev.id}_{i}")
                vars_by_key[(ev.id, i)] = var
                available_variable_count += 1
                charger_vars.setdefault((evc.charger.id, i), []).append(var)
                station_vars.setdefault((evc.station.id, i), []).append(var)

            if available_variable_count == 0:
                raise OptimizationError(f"EV {ev.id} has no overlapping energy slots.")

        # Each EV must receive enough energy to satisfy its target SOC.
        for evc in ev_contexts:
            energy_coeffs: list[int] = []
            energy_vars: list[cp_model.IntVar] = []
            for i, slot in enumerate(slots):
                var = vars_by_key.get((evc.ev.id, i))
                if var is None:
                    continue
                overlap_hours = self._slot_overlap_hours(
                    slot.timestamp, evc.ev.arrival_time, evc.ev.departure_time
                )
                coeff = int(round(overlap_hours * POWER_UNIT_KW / ENERGY_UNIT_KWH))
                if coeff <= 0:
                    continue
                energy_vars.append(var)
                energy_coeffs.append(coeff)

            required_units = int(math.ceil(evc.required_energy_kwh / ENERGY_UNIT_KWH - 1e-9))
            energy_expr = sum(v * c for v, c in zip(energy_vars, energy_coeffs))
            model.Add(energy_expr >= required_units)
            # Do not allow an objective (especially a green/renewable objective)
            # to "overcharge" an EV simply because extra energy is beneficial
            # in objective space. A one-power-unit tolerance is enough to
            # accommodate the 0.1 kW / partial-slot discretization.
            max_coeff = max(energy_coeffs)
            model.Add(energy_expr <= required_units + max_coeff - 1)

        # Charger power limits are embodied by variable upper bounds, while
        # station and grid limits constrain aggregated simultaneous power.
        for i, slot in enumerate(slots):
            all_vars = [v for (ev_id, idx), v in vars_by_key.items() if idx == i]
            total = model.NewIntVar(0, 10**9, f"slot_total_{i}")
            if all_vars:
                model.Add(total == sum(all_vars))
            else:
                model.Add(total == 0)
            slot_total.append(total)
            cap_units = int(math.floor(max(0.0, slot.grid_capacity_kw - slot.base_load_kw) / POWER_UNIT_KW + 1e-9))
            model.Add(total <= cap_units)

        for (charger_id, i), var_list in charger_vars.items():
            charger = next(evc.charger for evc in ev_contexts if evc.charger.id == charger_id)
            max_units = int(math.floor(charger.max_power_kw / POWER_UNIT_KW + 1e-9))
            model.Add(sum(var_list) <= max_units)

        for (station_id, i), var_list in station_vars.items():
            station = next(evc.station for evc in ev_contexts if evc.station.id == station_id)
            station_units = int(math.floor(station.capacity_kw / POWER_UNIT_KW + 1e-9))
            model.Add(sum(var_list) <= station_units)

        # GridSignals are soft signals. We penalize deviations rather than
        # making them hard feasibility constraints.
        objective_terms: list[cp_model.LinearExpr] = []
        objective_terms.extend(
            self._objective_terms(
                model=model,
                vars_by_key=vars_by_key,
                ev_contexts=ev_contexts,
                slots=slots,
                objective=objective,
                baseline=baseline,
            )
        )
        objective_terms.extend(
            self._grid_signal_penalty_terms(model, slot_total, slots, signals, baseline=baseline)
        )

        if not objective_terms:
            raise OptimizationError("Optimizer objective was empty.")

        model.Minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 20.0
        solver.parameters.num_search_workers = 4
        solver.parameters.random_seed = int(self.settings.seed)
        solver.parameters.log_search_progress = False

        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            if status == cp_model.INFEASIBLE:
                raise OptimizationError("No feasible charging schedule satisfies the hard constraints.")
            raise OptimizationError(f"Optimizer stopped without a usable solution (status={status}).")

        return {key: int(solver.Value(var)) for key, var in vars_by_key.items()}

    def _objective_terms(
        self,
        *,
        model: cp_model.CpModel,
        vars_by_key: dict[tuple[str, int], cp_model.IntVar],
        ev_contexts: list[EVContext],
        slots: list[SlotContext],
        objective: OperatorObjective,
        baseline: bool,
    ) -> list[cp_model.LinearExpr]:
        terms: list[cp_model.LinearExpr] = []
        if baseline:
            # Deterministic baseline: reward earlier power more strongly, with
            # no renewable/cost preference. This is the "charge immediately at
            # max feasible power" rule from architecture.md §6.
            max_index = max(1, len(slots) - 1)
            for evc in ev_contexts:
                urgency = self._urgency_weight(evc.ev)
                for i in range(len(slots)):
                    var = vars_by_key.get((evc.ev.id, i))
                    if var is None:
                        continue
                    overlap = self._slot_overlap_hours(
                        slots[i].timestamp, evc.ev.arrival_time, evc.ev.departure_time
                    )
                    if overlap <= 0:
                        continue
                    # Earlier time is cheaper in objective space; urgency
                    # keeps low-flexibility EVs earlier than high-flexibility EVs.
                    delay = i * (1 + urgency)
                    terms.append(var * delay)
            return terms

        # Candidate objective coefficients use paise/grams style integerized
        # costs so CP-SAT remains exact while keeping the weights interpretable.
        for evc in ev_contexts:
            ev = evc.ev
            preference = str(ev.preference)
            urgency = self._urgency_weight(ev)
            for i, slot in enumerate(slots):
                var = vars_by_key.get((ev.id, i))
                if var is None:
                    continue
                overlap_hours = self._slot_overlap_hours(slot.timestamp, ev.arrival_time, ev.departure_time)
                if overlap_hours <= 0:
                    continue
                energy_units = int(round(overlap_hours * POWER_UNIT_KW / ENERGY_UNIT_KWH))
                if energy_units <= 0:
                    continue

                cost_paise_per_var = max(1, int(round(energy_units * slot.electricity_price * 100)))
                carbon_grams_per_var = max(0, int(round(energy_units * slot.carbon_intensity * 1000)))
                renewable_bonus_per_var = int(round(energy_units * min(1.0, slot.renewable_kw / max(slot.base_load_kw, 1.0))))

                if objective == OperatorObjective.cheapest:
                    coeff = cost_paise_per_var * 10 + carbon_grams_per_var
                elif objective == OperatorObjective.greenest:
                    coeff = carbon_grams_per_var * 10 + cost_paise_per_var - renewable_bonus_per_var * 3
                else:  # balanced
                    coeff = cost_paise_per_var * 7 + carbon_grams_per_var * 3 - renewable_bonus_per_var * 2

                # Driver preference is a soft tie-breaker layered onto the
                # operator objective. Immediate drivers are favored earlier;
                # greenest/cheapest get a stronger domain-specific pull.
                if preference == "immediate":
                    coeff += i * 20
                elif preference == "cheapest":
                    coeff += cost_paise_per_var * 3
                elif preference == "greenest":
                    coeff += carbon_grams_per_var * 3 - renewable_bonus_per_var
                else:  # balanced
                    coeff += (cost_paise_per_var + carbon_grams_per_var) // 2

                # Low flexibility should be delayed less than high flexibility.
                coeff += i * urgency * 2
                terms.append(var * coeff)

        return terms

    @staticmethod
    def _urgency_weight(ev: EV) -> int:
        # Lower number = easier to move later. Non-flexible/low-flexibility
        # sessions receive stronger "stay earlier" pressure.
        return {
            "high": 0,
            "medium": 1,
            "low": 2,
            "non_flexible": 4,
        }.get(ev.flexibility, 1)

    @staticmethod
    def _slot_overlap_hours(timestamp: datetime, arrival: datetime, departure: datetime) -> float:
        slot_start = timestamp
        slot_end = slot_start + timedelta(minutes=SLOT_MINUTES)
        start = max(slot_start, arrival)
        end = min(slot_end, departure)
        if end <= start:
            return 0.0
        return (end - start).total_seconds() / 3600.0

    def _grid_signal_penalty_terms(
        self,
        model: cp_model.CpModel,
        slot_total: list[cp_model.IntVar],
        slots: list[SlotContext],
        signals: list[GridSignal],
        *,
        baseline: bool,
    ) -> list[cp_model.LinearExpr]:
        terms: list[cp_model.LinearExpr] = []
        # Keep the baseline faithful to "immediate charging". Grid signals are
        # only optimization guidance for the candidate.
        if baseline:
            return terms

        for signal_index, signal in enumerate(signals):
            recommended_units = int(round(signal.recommended_ev_load_kw / POWER_UNIT_KW))
            for i, slot in enumerate(slots):
                if not (signal.start_time <= slot.timestamp < signal.end_time):
                    continue
                deviation = model.NewIntVar(0, 10**9, f"signal_dev_{signal_index}_{i}")
                if signal.signal_operator == "lte":
                    model.Add(deviation >= slot_total[i] - recommended_units)
                else:  # gte
                    model.Add(deviation >= recommended_units - slot_total[i])
                model.Add(deviation >= 0)
                # Large enough to influence decisions, but still a soft signal.
                terms.append(deviation * 5)
        return terms

    # ------------------------------------------------------------------
    # Schedule + metrics
    # ------------------------------------------------------------------

    def _matrix_to_schedule(
        self,
        ev_contexts: list[EVContext],
        slots: list[SlotContext],
        power_matrix: dict[tuple[str, int], int],
    ) -> list[SchedulePoint]:
        by_ev = {evc.ev.id: evc for evc in ev_contexts}

        # Build raw charging entries first. Renewable generation is a shared
        # network resource per time slot, so it must be allocated across all EV
        # loads in that slot rather than counted independently for each EV.
        raw_entries: list[dict] = []
        for (ev_id, i), units in sorted(
            power_matrix.items(), key=lambda item: (item[0][0], item[0][1])
        ):
            if units <= 0:
                continue
            evc = by_ev[ev_id]
            slot = slots[i]
            overlap_hours = self._slot_overlap_hours(
                slot.timestamp, evc.ev.arrival_time, evc.ev.departure_time
            )
            power_kw = round(units * POWER_UNIT_KW, 1)
            energy_kwh = round(power_kw * overlap_hours, 4)
            raw_entries.append(
                {
                    "ev_id": ev_id,
                    "timestamp": slot.timestamp,
                    "charging_power_kw": power_kw,
                    "energy_kwh": energy_kwh,
                    "slot": slot,
                }
            )

        # Allocate each slot's available renewable energy proportionally to
        # charging energy. This guarantees that aggregate renewable energy
        # attributed to EV charging never exceeds renewable generation available
        # in that slot.
        by_timestamp: dict[datetime, list[dict]] = {}
        for raw in raw_entries:
            by_timestamp.setdefault(raw["timestamp"], []).append(raw)

        entries: list[SchedulePoint] = []
        for timestamp in sorted(by_timestamp):
            group = by_timestamp[timestamp]
            slot = group[0]["slot"]
            total_energy = sum(item["energy_kwh"] for item in group)
            renewable_available = max(0.0, slot.renewable_kw) * (SLOT_MINUTES / 60.0)
            renewable_available = min(renewable_available, total_energy)

            for raw in group:
                if total_energy > 0.0:
                    share = raw["energy_kwh"] / total_energy
                else:
                    share = 0.0
                renewable_energy_kwh = round(renewable_available * share, 4)
                grid_energy_kwh = round(
                    max(0.0, raw["energy_kwh"] - renewable_energy_kwh), 4
                )
                cost = round(raw["energy_kwh"] * slot.electricity_price, 4)
                co2 = round(grid_energy_kwh * slot.carbon_intensity, 4)
                entries.append(
                    SchedulePoint(
                        ev_id=raw["ev_id"],
                        timestamp=raw["timestamp"],
                        charging_power_kw=raw["charging_power_kw"],
                        energy_kwh=raw["energy_kwh"],
                        renewable_energy_kwh=renewable_energy_kwh,
                        grid_energy_kwh=grid_energy_kwh,
                        cost=cost,
                        co2_kg=co2,
                    )
                )
        return entries

    @staticmethod
    def _metrics(entries: list[SchedulePoint], slots: list[SlotContext]) -> Metrics:
        if not entries:
            return Metrics(peak_kw=0.0, cost=0.0, renewable_share_pct=0.0, co2_kg=0.0)

        by_ts: dict[datetime, float] = {}
        total_energy = 0.0
        renewable_energy = 0.0
        total_cost = 0.0
        total_co2 = 0.0
        for entry in entries:
            by_ts[entry.timestamp] = by_ts.get(entry.timestamp, 0.0) + entry.charging_power_kw
            total_energy += entry.energy_kwh
            renewable_energy += entry.renewable_energy_kwh
            total_cost += entry.cost
            total_co2 += entry.co2_kg

        renewable_share = (renewable_energy / total_energy * 100.0) if total_energy > 0 else 0.0
        return Metrics(
            peak_kw=round(max(by_ts.values(), default=0.0), 2),
            cost=round(total_cost, 2),
            renewable_share_pct=round(renewable_share, 2),
            co2_kg=round(total_co2, 2),
        )
