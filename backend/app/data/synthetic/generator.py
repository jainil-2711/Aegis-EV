"""
Aegis — Synthetic Data Generator (P1)

Produces a deterministic demo dataset per data-spec.md SS16:
    40 EVs, 5-8 stations, 20-30 chargers, 24h horizon, 30-min slots.

Determinism contract: calling generate_full_dataset() twice with the same
seed and demo_day MUST produce byte-identical output. No wall-clock time,
no os.urandom, no unordered set/dict iteration is used for anything that
affects generated values. This is what lets scripts/seed_demo.py be
re-run safely (architecture.md SS16, PRD.md SS11).

Charger assignment is decided here, at seed time, and is treated as fixed
input to the optimizer from then on (data-spec.md SS3). P1 assigns only the
physical charger capability; P2 owns time-slot charging occupancy/scheduling
and must not reassign an EV to a different charger_id.
"""

import random
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.config import Settings

# ---------------------------------------------------------------------------
# Profile definitions (PRD.md SS11 / architecture "genuinely different
# flexibility classes")
# ---------------------------------------------------------------------------

# Each profile controls: arrival hour range, dwell (departure - arrival)
# range in hours, battery size range, SOC gap, preference weighting.
PROFILES = {
    "commuter": {
        "weight": 0.40,
        "arrival_hour_range": (7.0, 10.0),
        "dwell_hours_range": (7.0, 9.0),
        "battery_kwh_range": (40.0, 75.0),
        "current_soc_range": (15.0, 45.0),
        "target_soc_range": (70.0, 95.0),
        "max_charge_kw_range": (10.0, 11.0),
        "preferences": ["balanced", "cheapest", "greenest"],
    },
    "quick_stop": {
        "weight": 0.25,
        "arrival_hour_range": (8.0, 20.0),
        "dwell_hours_range": (1.0, 1.5),
        "battery_kwh_range": (40.0, 80.0),
        "current_soc_range": (20.0, 50.0),
        "target_soc_range": (60.0, 85.0),
        "max_charge_kw_range": (60.0, 120.0),
        "preferences": ["immediate", "cheapest"],
    },
    "fleet": {
        "weight": 0.20,
        "arrival_hour_range": (14.0, 15.0),
        "dwell_hours_range": (7.5, 9.0),
        "battery_kwh_range": (60.0, 100.0),
        "current_soc_range": (10.0, 35.0),
        "target_soc_range": (85.0, 100.0),
        "max_charge_kw_range": (14.0, 22.0),
        "preferences": ["greenest", "balanced"],
    },
    "urgent": {
        "weight": 0.15,
        "arrival_hour_range": (0.0, 21.5),
        "dwell_hours_range": (1.75, 2.5),
        "battery_kwh_range": (40.0, 90.0),
        "current_soc_range": (5.0, 20.0),
        "target_soc_range": (70.0, 95.0),
        "max_charge_kw_range": (65.0, 150.0),
        "preferences": ["immediate"],
    },
}

CONNECTOR_TYPES = ["type2", "ccs", "chademo", "other"]
CONNECTOR_WEIGHTS = [0.35, 0.45, 0.15, 0.05]


@dataclass
class SyntheticDataset:
    stations: list[dict] = field(default_factory=list)
    chargers: list[dict] = field(default_factory=list)
    evs: list[dict] = field(default_factory=list)
    energy_slots: list[dict] = field(default_factory=list)


def _weighted_choice(rng: random.Random, options: list[str], weights: list[float]) -> str:
    return rng.choices(options, weights=weights, k=1)[0]


def generate_stations(rng: random.Random, settings: Settings) -> list[dict]:
    stations = []
    for i in range(settings.num_stations):
        stations.append(
            {
                "id": f"STN-{i + 1:02d}",
                "name": f"Aegis Station {i + 1}",
                # capacity assigned after chargers are known; placeholder here
                "capacity_kw": 0.0,
                "charger_count": 0,
            }
        )
    return stations


def generate_chargers(rng: random.Random, settings: Settings, stations: list[dict]) -> list[dict]:
    chargers = []
    station_ids = [s["id"] for s in stations]
    # Use a deterministic but realistic charger mix rather than allowing a
    # random draw to accidentally produce a network with no suitable high-power
    # chargers for quick-stop/urgent sessions. This describes the network type;
    # it is not derived from optimizer outcomes.
    canonical_pool = [150.0] * 4 + [120.0] * 8 + [50.0] * 4 + [22.0] * 4 + [11.0] * 2 + [7.0] * 2
    if settings.num_chargers <= len(canonical_pool):
        power_pool = canonical_pool[: settings.num_chargers]
    else:
        power_pool = canonical_pool + [22.0] * (settings.num_chargers - len(canonical_pool))
    rng.shuffle(power_pool)

    for i in range(settings.num_chargers):
        station_id = station_ids[i % len(station_ids)]
        connector_type = _weighted_choice(rng, CONNECTOR_TYPES, CONNECTOR_WEIGHTS)
        max_power_kw = power_pool[i]
        # 90% available, 5% occupied, 5% offline/maintenance — deterministic
        # given the seeded rng, not a live operational signal.
        status = _weighted_choice(
            rng,
            ["available", "occupied", "offline", "maintenance"],
            [0.85, 0.08, 0.04, 0.03],
        )
        chargers.append(
            {
                "id": f"CHG-{i + 1:03d}",
                "station_id": station_id,
                "max_power_kw": max_power_kw,
                "connector_type": connector_type,
                "status": status,
            }
        )

    # Backfill station capacity/charger_count from actual assignment so the
    # two datasets are always consistent (no station under/over-subscribed
    # relative to its own charger list).
    for station in stations:
        assigned = [c for c in chargers if c["station_id"] == station["id"]]
        station["charger_count"] = len(assigned)
        station["capacity_kw"] = round(sum(c["max_power_kw"] for c in assigned), 1)

    return chargers


def _pick_profile(rng: random.Random) -> str:
    names = list(PROFILES.keys())
    weights = [PROFILES[n]["weight"] for n in names]
    return _weighted_choice(rng, names, weights)


def compute_flexibility(
    arrival_time: datetime,
    departure_time: datetime,
    required_energy_kwh: float,
    effective_power_kw: float,
) -> str:
    """
    Flexibility = required charging duration vs. available connection window
    (data-spec.md SS4). Deterministic rule, documented in
    docs/DEV_WORKFLOWS.md as a P1 assumption:

        required_hours >= window_hours          -> non_flexible
        slack_ratio >= 0.66                      -> high
        slack_ratio >= 0.33                      -> medium
        else                                      -> low

    where slack_ratio = (window_hours - required_hours) / window_hours
    """
    window_hours = (departure_time - arrival_time).total_seconds() / 3600.0
    if effective_power_kw <= 0 or window_hours <= 0:
        return "non_flexible"

    required_hours = required_energy_kwh / effective_power_kw

    if required_hours >= window_hours:
        return "non_flexible"

    slack_ratio = (window_hours - required_hours) / window_hours
    if slack_ratio >= 0.66:
        return "high"
    if slack_ratio >= 0.33:
        return "medium"
    return "low"


def _required_energy_kwh(ev: dict) -> float:
    return (
        ev["battery_capacity_kwh"]
        * (ev["target_soc"] - ev["current_soc"])
        / 100.0
        / ev["efficiency"]
    )


def _required_power_kw(ev: dict, horizon_start: datetime, horizon_end: datetime) -> float:
    start = max(ev["arrival_time"], horizon_start)
    end = min(ev["departure_time"], horizon_end)
    available_hours = max(0.0, (end - start).total_seconds() / 3600.0)
    if available_hours <= 0.0:
        return float("inf")
    return _required_energy_kwh(ev) / available_hours

def _assign_chargers(
    evs: list[dict],
    chargers: list[dict],
    horizon_start: datetime,
    horizon_end: datetime,
) -> None:
    """Assign each EV to a fixed physically suitable charger.

    Assignment uses only generated EV requirements and charger capabilities.
    It does not inspect optimizer results or scheduling outcomes.

    Suitable chargers are deterministically load-balanced by the number of
    already assigned EV connection windows that overlap the current request.
    This prevents the synthetic generator from creating artificial bottlenecks
    by placing every compatible EV on the smallest charger.
    """
    assignable = [c for c in chargers if c["status"] != "offline"] or chargers
    ordered = sorted(evs, key=lambda e: (e["arrival_time"], e["id"]))

    assigned: dict[str, list[dict]] = {c["id"]: [] for c in assignable}

    def overlaps(a: dict, b: dict) -> bool:
        return (
            a["arrival_time"] < b["departure_time"]
            and b["arrival_time"] < a["departure_time"]
        )

    for ev in ordered:
        required_power_kw = _required_power_kw(
            ev, horizon_start, horizon_end
        )

        candidates = [
            c
            for c in assignable
            if c["max_power_kw"] + 1e-9 >= required_power_kw
        ]

        if not candidates:
            raise ValueError(
                f"Unable to assign a physically suitable charger to {ev['id']} "
                "without modifying its generated request."
            )

        def score(charger: dict) -> tuple:
            existing = assigned[charger["id"]]
            overlap_count = sum(
                1 for other in existing if overlaps(ev, other)
            )

            return (
                overlap_count,
                len(existing),
                charger["max_power_kw"],
                charger["id"],
            )

        charger = min(candidates, key=score)
        ev["charger_id"] = charger["id"]
        assigned[charger["id"]].append(ev)


def generate_evs(
    rng: random.Random,
    settings: Settings,
    chargers: list[dict],
    demo_day: datetime,
) -> list[dict]:
    evs: list[dict] = []
    horizon_end = demo_day + timedelta(hours=settings.horizon_hours)

    for i in range(settings.num_evs):
        profile_name = _pick_profile(rng)
        profile = PROFILES[profile_name]

        arrival_hour = rng.uniform(*profile["arrival_hour_range"])
        dwell_hours = rng.uniform(*profile["dwell_hours_range"])
        arrival_time = demo_day + timedelta(hours=arrival_hour)
        departure_time = arrival_time + timedelta(hours=dwell_hours)

        battery_capacity_kwh = round(rng.uniform(*profile["battery_kwh_range"]), 1)
        current_soc = round(rng.uniform(*profile["current_soc_range"]), 1)
        efficiency = round(rng.uniform(0.88, 0.97), 3)
        max_charge_kw = round(rng.uniform(*profile["max_charge_kw_range"]), 1)
        preference = rng.choice(profile["preferences"])

        # Generate the driver's target independently of the optimizer. We use
        # deterministic rejection sampling against only the EV's own physical
        # request (battery, requested charge rate and dwell window), so a
        # realistic driver request is retained rather than being altered after
        # seeing solver capacity or metrics.
        target_soc = None
        max_target = profile["target_soc_range"][1]
        min_target = max(profile["target_soc_range"][0], current_soc + 5.0)
        for _ in range(40):
            candidate_target = round(rng.uniform(min_target, max_target), 1)
            candidate_energy = (
                battery_capacity_kwh
                * (candidate_target - current_soc)
                / 100.0
                / efficiency
            )
            if candidate_energy <= max_charge_kw * dwell_hours * 0.90 + 1e-9:
                target_soc = candidate_target
                break
        if target_soc is None:
            raise ValueError(
                f"Unable to generate a physically coherent request for {profile_name} "
                f"without modifying optimizer inputs."
            )

        evs.append(
            {
                "id": f"EV-{i + 101}",
                "battery_capacity_kwh": battery_capacity_kwh,
                "current_soc": current_soc,
                "target_soc": target_soc,
                "arrival_time": arrival_time,
                "departure_time": departure_time,
                "max_charge_kw": max_charge_kw,
                "efficiency": efficiency,
                "preference": preference,
                "charger_id": "",
                "profile": profile_name,
                "data_source": "synthetic",
            }
        )

    _assign_chargers(evs, chargers, demo_day, horizon_end)

    for ev in evs:
        # Flexibility uses the generated request and the EV's requested
        # charging rate. It is not tuned to a solver result.
        ev["flexibility"] = compute_flexibility(
            ev["arrival_time"],
            ev["departure_time"],
            _required_energy_kwh(ev),
            ev["max_charge_kw"],
        )

    return evs

def generate_energy_slots(rng: random.Random, settings: Settings, demo_day: datetime) -> list[dict]:
    """
    48 half-hour slots across the 24h demo horizon. Deterministic curves:
      - base_load_kw: two-peak daily demand curve (morning + evening).
      - renewable_kw: solar bump around midday plus a small wind baseline
        with bounded deterministic noise (rng, not wall-clock random).
      - grid_capacity_kw: constant headroom ceiling for the demo.
      - electricity_price / carbon_intensity: move inversely with
        renewable share, matching PRD.md SS8 pricing direction (not the
        authoritative pricing engine — that is P2's engine/pricing.py).
    """
    slot_count = int(settings.horizon_hours * 60 / settings.slot_minutes)
    grid_capacity_kw = 2200.0
    base_price = 8.0  # INR/kWh baseline
    base_carbon = 0.75  # kgCO2/kWh at zero renewable share

    slots = []
    for i in range(slot_count):
        ts = demo_day + timedelta(minutes=i * settings.slot_minutes)
        hour = ts.hour + ts.minute / 60.0

        # Two-hump base demand curve (morning ~8h, evening ~19h), scaled to
        # a plausible city-block demand range.
        morning = 250 * _gaussian_bump(hour, peak=8.5, width=2.0)
        evening = 400 * _gaussian_bump(hour, peak=19.0, width=2.5)
        base_load_kw = round(300 + morning + evening + rng.uniform(-15, 15), 1)

        # Solar bump around midday + small constant wind + bounded noise.
        solar = 350 * _gaussian_bump(hour, peak=13.0, width=3.0)
        wind = 60 + 20 * _gaussian_bump(hour, peak=3.0, width=6.0)
        renewable_kw = round(max(0.0, solar + wind + rng.uniform(-10, 10)), 1)

        renewable_share = min(1.0, renewable_kw / max(base_load_kw, 1.0))

        electricity_price = round(
            base_price * (1.15 - 0.35 * renewable_share) + rng.uniform(-0.15, 0.15), 2
        )
        carbon_intensity = round(
            base_carbon * (1.0 - 0.7 * renewable_share) + rng.uniform(-0.02, 0.02), 3
        )

        slots.append(
            {
                "timestamp": ts,
                "base_load_kw": base_load_kw,
                "renewable_kw": renewable_kw,
                "grid_capacity_kw": grid_capacity_kw,
                "electricity_price": max(electricity_price, 1.0),
                "carbon_intensity": max(carbon_intensity, 0.05),
            }
        )

    return slots


def _gaussian_bump(x: float, peak: float, width: float) -> float:
    """Simple bounded bump function in [0, 1], deterministic, no imports
    beyond math — used to shape daily demand/renewable curves."""
    
    return math.exp(-((x - peak) ** 2) / (2 * width**2))


def generate_full_dataset(settings: Settings) -> SyntheticDataset:
    rng = random.Random(settings.seed)
    demo_day = datetime.fromisoformat(settings.demo_day)

    stations = generate_stations(rng, settings)
    chargers = generate_chargers(rng, settings, stations)
    evs = generate_evs(rng, settings, chargers, demo_day)
    energy_slots = generate_energy_slots(rng, settings, demo_day)

    return SyntheticDataset(
        stations=stations, chargers=chargers, evs=evs, energy_slots=energy_slots
    )
