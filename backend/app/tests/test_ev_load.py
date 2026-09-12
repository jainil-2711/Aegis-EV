from datetime import datetime

from app.models.charger import Charger
from app.models.charging_schedule_entry import ChargingScheduleEntry
from app.models.ev import EV
from app.models.optimization_run import OptimizationRun
from app.services.shared.ev_load import get_ev_load


def _make_ev(db_session, **overrides):
    defaults = dict(
        id="EV-1",
        battery_capacity_kwh=60.0,
        current_soc=20.0,
        target_soc=90.0,
        arrival_time=datetime(2026, 9, 12, 8, 0),
        departure_time=datetime(2026, 9, 12, 18, 0),
        max_charge_kw=11.0,
        efficiency=0.9,
        preference="balanced",
        charger_id="CHG-1",
        flexibility="high",
        profile="commuter",
        data_source="synthetic",
    )
    defaults.update(overrides)
    ev = EV(**defaults)
    db_session.add(ev)
    return ev


def test_naive_fallback_used_when_no_applied_run(db_session, settings):
    db_session.add(Charger(id="CHG-1", station_id="STN-1", max_power_kw=11.0, connector_type="type2", status="available"))
    db_session.add_all([
        __import__("app.models.station", fromlist=["Station"]).Station(
            id="STN-1", name="S1", capacity_kw=11.0, charger_count=1
        )
    ])
    _make_ev(db_session)
    db_session.commit()

    # "now" inside the EV's connection window -> should show nonzero load
    now = datetime(2026, 9, 12, 10, 0)
    result = get_ev_load(db_session, settings, now=now)

    assert result.source == "naive_fallback"
    assert result.current_ev_load_kw > 0
    assert result.peak_ev_load_kw >= result.current_ev_load_kw


def test_naive_fallback_zero_when_no_evs_connected(db_session, settings):
    now = datetime(2026, 9, 12, 3, 0)
    result = get_ev_load(db_session, settings, now=now)
    assert result.source == "naive_fallback"
    assert result.current_ev_load_kw == 0.0
    assert result.scheduled_ev_load_kw == 0.0


def test_applied_schedule_takes_priority_over_fallback(db_session, settings):
    run = OptimizationRun(id="RUN-1", mode="balanced", status="applied")
    db_session.add(run)

    slot_a = datetime(2026, 9, 12, 8, 0)
    slot_b = datetime(2026, 9, 12, 8, 30)

    db_session.add_all(
        [
            ChargingScheduleEntry(
                optimization_run_id="RUN-1",
                ev_id="EV-1",
                timestamp=slot_a,
                charging_power_kw=7.0,
                energy_kwh=3.5,
                renewable_energy_kwh=2.0,
                grid_energy_kwh=1.5,
                cost=10.0,
                co2_kg=1.0,
            ),
            ChargingScheduleEntry(
                optimization_run_id="RUN-1",
                ev_id="EV-1",
                timestamp=slot_b,
                charging_power_kw=11.0,
                energy_kwh=5.5,
                renewable_energy_kwh=4.0,
                grid_energy_kwh=1.5,
                cost=12.0,
                co2_kg=1.2,
            ),
        ]
    )
    db_session.commit()

    result = get_ev_load(db_session, settings, now=slot_a)

    assert result.source == "applied_schedule"
    assert result.current_ev_load_kw == 7.0
    assert result.scheduled_ev_load_kw == 11.0
    assert result.peak_ev_load_kw == 11.0
