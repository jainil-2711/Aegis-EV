from app.data.synthetic.generator import compute_flexibility, generate_full_dataset
from datetime import datetime, timedelta


def test_dataset_sizes_match_settings(settings):
    dataset = generate_full_dataset(settings)
    assert len(dataset.evs) == settings.num_evs
    assert len(dataset.stations) == settings.num_stations
    assert len(dataset.chargers) == settings.num_chargers
    assert len(dataset.energy_slots) == settings.horizon_hours * 60 / settings.slot_minutes


def test_generation_is_deterministic(settings):
    d1 = generate_full_dataset(settings)
    d2 = generate_full_dataset(settings)
    assert d1.evs == d2.evs
    assert d1.stations == d2.stations
    assert d1.chargers == d2.chargers
    assert d1.energy_slots == d2.energy_slots


def test_ev_core_invariants(settings):
    """rules.md SS17 core invariants."""
    dataset = generate_full_dataset(settings)
    charger_ids = {c["id"] for c in dataset.chargers}

    for ev in dataset.evs:
        assert ev["current_soc"] <= ev["target_soc"]
        assert ev["arrival_time"] < ev["departure_time"]
        assert ev["charger_id"] in charger_ids
        assert 0 < ev["efficiency"] <= 1
        assert ev["max_charge_kw"] > 0


def test_station_charger_counts_consistent(settings):
    dataset = generate_full_dataset(settings)
    for station in dataset.stations:
        assigned = [c for c in dataset.chargers if c["station_id"] == station["id"]]
        assert station["charger_count"] == len(assigned)


def test_flexibility_classification():
    arrival = datetime(2026, 9, 12, 8, 0)

    # Required 2h charge in a 2h window -> non_flexible (no slack)
    assert compute_flexibility(arrival, arrival + timedelta(hours=2), 20.0, 10.0) == "non_flexible"

    # Required 2h charge in a 10h window -> slack_ratio 0.8 -> high
    assert compute_flexibility(arrival, arrival + timedelta(hours=10), 20.0, 10.0) == "high"

    # Required 4h charge in a 6h window -> slack_ratio 0.33 -> medium
    assert compute_flexibility(arrival, arrival + timedelta(hours=6), 40.0, 10.0) == "medium"


def test_energy_slots_cover_full_horizon(settings):
    dataset = generate_full_dataset(settings)
    timestamps = [s["timestamp"] for s in dataset.energy_slots]
    assert timestamps == sorted(timestamps)
    assert timestamps[0].hour == 0 and timestamps[0].minute == 0
    span = timestamps[-1] - timestamps[0]
    assert span == timedelta(hours=settings.horizon_hours - settings.slot_minutes / 60)


def test_renewable_and_price_bounds(settings):
    dataset = generate_full_dataset(settings)
    for slot in dataset.energy_slots:
        assert slot["renewable_kw"] >= 0
        assert slot["electricity_price"] >= 1.0
        assert 0 < slot["carbon_intensity"] < 1.0
        assert slot["grid_capacity_kw"] > 0

def test_generated_ev_targets_are_feasible_within_demo_horizon(settings):
    """Every seeded EV must be schedulable without violating hard constraints."""
    dataset = generate_full_dataset(settings)
    charger_by_id = {c["id"]: c for c in dataset.chargers}
    horizon_end = dataset.energy_slots[-1]["timestamp"] + timedelta(minutes=settings.slot_minutes)

    for ev in dataset.evs:
        charger = charger_by_id[ev["charger_id"]]
        effective_power_kw = min(ev["max_charge_kw"], charger["max_power_kw"])
        required_energy_kwh = (
            ev["battery_capacity_kwh"]
            * (ev["target_soc"] - ev["current_soc"])
            / 100.0
            / ev["efficiency"]
        )
        start = max(ev["arrival_time"], dataset.energy_slots[0]["timestamp"])
        end = min(ev["departure_time"], horizon_end)
        available_hours = max(0.0, (end - start).total_seconds() / 3600.0)
        assert required_energy_kwh <= effective_power_kw * available_hours + 0.02



def test_assigned_chargers_can_deliver_each_generated_request(settings):
    """P1 assigns physical capability; P2 owns time-slot occupancy scheduling."""
    dataset = generate_full_dataset(settings)
    charger_by_id = {c["id"]: c for c in dataset.chargers}
    for ev in dataset.evs:
        charger = charger_by_id[ev["charger_id"]]
        required_energy_kwh = (
            ev["battery_capacity_kwh"]
            * (ev["target_soc"] - ev["current_soc"])
            / 100.0
            / ev["efficiency"]
        )
        available_hours = (ev["departure_time"] - ev["arrival_time"]).total_seconds() / 3600.0
        effective_power_kw = min(ev["max_charge_kw"], charger["max_power_kw"])
        assert required_energy_kwh <= effective_power_kw * available_hours + 1e-6


def test_multiple_deterministic_seeds_produce_valid_independent_data(settings):
    """The optimizer/demo must not depend on a single hand-tuned seed."""
    from copy import copy

    seeds = [7, 42, 123, 999]
    seed_settings = []
    for seed in seeds:
        variant = copy(settings)
        variant.seed = seed
        seed_settings.append(variant)
    datasets = [generate_full_dataset(variant) for variant in seed_settings]

    for dataset in datasets:
        charger_ids = {c["id"] for c in dataset.chargers}
        for ev in dataset.evs:
            assert ev["charger_id"] in charger_ids
            assert ev["current_soc"] < ev["target_soc"] <= 100.0
            required_energy_kwh = (
                ev["battery_capacity_kwh"]
                * (ev["target_soc"] - ev["current_soc"])
                / 100.0
                / ev["efficiency"]
            )
            charger = next(c for c in dataset.chargers if c["id"] == ev["charger_id"])
            available_hours = max(
                0.0,
                (ev["departure_time"] - ev["arrival_time"]).total_seconds() / 3600.0,
            )
            assert required_energy_kwh <= min(ev["max_charge_kw"], charger["max_power_kw"]) * available_hours + 1e-6

    # Independent seeds should produce genuinely different EV fleets.
    assert datasets[0].evs != datasets[1].evs
    assert datasets[1].evs != datasets[2].evs
