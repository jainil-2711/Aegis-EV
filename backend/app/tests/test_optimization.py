import importlib.util
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data.synthetic.generator import generate_full_dataset
from app.database import Base, get_db
from app.main import app
from app.schemas.enums import OperatorObjective
from app.models.charger import Charger
from app.models.energy_slot import EnergySlot
from app.models.ev import EV
from app.models.grid_signal import GridSignal
from app.models.station import Station
from app.services.optimization.optimizer import OptimizationError, OptimizationService
from app.engine.carbon import co2_kg_from_grid, reduction_pct, renewable_share_pct
from app.engine.green_score import calculate_green_score

ORTOOLS_AVAILABLE = importlib.util.find_spec("ortools") is not None


@pytest.fixture()
def optimizer_client(settings):
    from app import models  # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    dataset = generate_full_dataset(settings)
    db = TestingSessionLocal()
    from app.models.charger import Charger
    from app.models.energy_slot import EnergySlot
    from app.models.ev import EV
    from app.models.station import Station

    db.bulk_insert_mappings(Station, dataset.stations)
    db.bulk_insert_mappings(Charger, dataset.chargers)
    db.bulk_insert_mappings(EV, dataset.evs)
    db.bulk_insert_mappings(EnergySlot, dataset.energy_slots)
    db.commit()
    db.close()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="OR-Tools not installed in the test environment")
def test_optimizer_produces_candidate_and_baseline(optimizer_client):
    response = optimizer_client.post(
        "/api/optimization/run",
        json={"mode": "balanced", "scenario": "normal"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "candidate"
    assert body["mode"] == "balanced"
    assert body["baseline"]["peak_kw"] >= 0
    assert body["candidate"]["peak_kw"] >= 0
    assert body["candidate"]["cost"] >= 0
    assert body["candidate"]["renewable_share_pct"] >= 0
    assert 0 <= body["candidate"]["renewable_share_pct"] <= 100
    assert 0 <= body["baseline"]["renewable_share_pct"] <= 100
    assert body["schedule"]

    run_id = body["id"]
    detail = optimizer_client.get(f"/api/optimization/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "candidate"


@pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="OR-Tools not installed in the test environment")
def test_schedule_renewable_attribution_does_not_exceed_slot_generation(optimizer_client, settings):
    response = optimizer_client.post(
        "/api/optimization/run",
        json={"mode": "balanced", "scenario": "normal"},
    )
    assert response.status_code == 200
    body = response.json()

    # Use the deterministic synthetic slot data as the network-level renewable
    # ceiling. Charging entries share this resource; it cannot be counted in
    # full independently for every EV in the same slot.
    # Read the generated dataset through a fresh service-independent path.
    from app.data.synthetic.generator import generate_full_dataset

    dataset = generate_full_dataset(settings)
    renewable_by_ts = {
        slot["timestamp"].isoformat(): slot["renewable_kw"] * (settings.slot_minutes / 60.0)
        for slot in dataset.energy_slots
    }

    attributed: dict[str, float] = {}
    for entry in body["schedule"]:
        attributed[entry["timestamp"]] = attributed.get(entry["timestamp"], 0.0) + entry["renewable_energy_kwh"]

    for timestamp, energy in attributed.items():
        assert energy <= renewable_by_ts[timestamp] + 0.01


@pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="OR-Tools not installed in the test environment")
def test_run_does_not_auto_activate_and_apply_transitions_state(optimizer_client):
    response = optimizer_client.post("/api/optimization/run", json={"mode": "cheapest"})
    assert response.status_code == 200
    run_id = response.json()["id"]

    before = optimizer_client.get("/api/optimization/schedule")
    assert before.status_code == 404

    applied = optimizer_client.post(
        "/api/optimization/apply",
        json={"optimization_run_id": run_id},
    )
    assert applied.status_code == 200
    assert applied.json()["status"] == "applied"

    after = optimizer_client.get("/api/optimization/schedule")
    assert after.status_code == 200
    assert after.json()["optimization_run_id"] == run_id
    assert after.json()["status"] == "applied"


@pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="OR-Tools not installed in the test environment")
def test_second_apply_supersedes_previous_candidate(optimizer_client):
    first = optimizer_client.post("/api/optimization/run", json={"mode": "balanced"}).json()["id"]
    optimizer_client.post("/api/optimization/apply", json={"optimization_run_id": first})

    second = optimizer_client.post("/api/optimization/run", json={"mode": "greenest"}).json()["id"]
    applied = optimizer_client.post("/api/optimization/apply", json={"optimization_run_id": second})
    assert applied.status_code == 200
    assert applied.json()["superseded_run_id"] == first

    first_detail = optimizer_client.get(f"/api/optimization/{first}")
    assert first_detail.status_code == 200
    assert first_detail.json()["status"] == "superseded"


@pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="OR-Tools not installed in the test environment")
def test_grid_signal_changes_candidate_schedule_when_soft_guidance_is_material(optimizer_client, settings):
    """A published GridSignal must materially influence the candidate schedule.

    This uses a tiny deterministic network: the first slot is cheaper, while a
    zero-load LTE signal covers only that slot. The signal remains soft, but its
    penalty is intentionally large enough to outweigh the price advantage and
    shift the flexible EV into the later slot.
    """
    from app import models  # noqa: F401
    # Reuse the TestClient application's in-memory DB through its dependency
    # override by getting the overridden session factory from a request path is
    # awkward, so build the scenario via the same isolated database used by the
    # fixture and replace the fixture's large generated dataset with a minimal
    # one through direct SQL deletes/inserts.
    from app.database import get_db
    from sqlalchemy import delete

    # Recover the fixture's active session factory from the dependency override.
    db_dependency = app.dependency_overrides[get_db]
    db = next(db_dependency())
    try:
        for model in (GridSignal, EV, Charger, Station, EnergySlot):
            db.execute(delete(model))
        db.commit()

        station = Station(id="ST-TEST", name="Test Station", capacity_kw=10.0, charger_count=1)
        charger = Charger(
            id="CH-TEST",
            station_id=station.id,
            max_power_kw=10.0,
            connector_type="ccs",
            status="available",
        )
        ev = EV(
            id="EV-TEST",
            battery_capacity_kwh=10.0,
            current_soc=0.0,
            target_soc=50.0,
            arrival_time=datetime(2026, 9, 12, 12, 0),
            departure_time=datetime(2026, 9, 12, 13, 0),
            max_charge_kw=10.0,
            efficiency=1.0,
            preference="cheapest",
            charger_id=charger.id,
            flexibility="high",
            profile="test",
            data_source="synthetic",
        )
        slots = [
            EnergySlot(
                timestamp=datetime(2026, 9, 12, 12, 0),
                base_load_kw=0.0,
                renewable_kw=0.0,
                grid_capacity_kw=10.0,
                electricity_price=5.0,
                carbon_intensity=0.75,
            ),
            EnergySlot(
                timestamp=datetime(2026, 9, 12, 12, 30),
                base_load_kw=0.0,
                renewable_kw=0.0,
                grid_capacity_kw=10.0,
                electricity_price=10.0,
                carbon_intensity=0.75,
            ),
        ]
        db.add_all([station, charger, ev, *slots])
        db.commit()

        no_signal = OptimizationService(db, settings).run(OperatorObjective.cheapest)
        no_signal_times = {point.timestamp for point in no_signal.candidate_schedule}
        assert no_signal_times == {datetime(2026, 9, 12, 12, 0)}

        db.add(
            GridSignal(
                start_time=datetime(2026, 9, 12, 12, 0),
                end_time=datetime(2026, 9, 12, 12, 30),
                condition="high_demand",
                recommended_ev_load_kw=0.0,
                signal_operator="lte",
                renewable_availability="low",
            )
        )
        db.commit()

        signaled = OptimizationService(db, settings).run(OperatorObjective.cheapest)
        signaled_times = {point.timestamp for point in signaled.candidate_schedule}
        assert signaled_times == {datetime(2026, 9, 12, 12, 30)}
    finally:
        db.close()


def test_environmental_accounting_formulas_are_consistent():
    assert renewable_share_pct(60.0, 20.0) == pytest.approx(33.3333333333)
    assert renewable_share_pct(60.0, 100.0) == 100.0
    assert renewable_share_pct(0.0, 20.0) == 0.0

    assert co2_kg_from_grid(40.0, 0.65) == pytest.approx(26.0)
    assert reduction_pct(100.0, 70.0) == pytest.approx(30.0)
    assert reduction_pct(0.0, 70.0) == 0.0

    score = calculate_green_score(
        renewable_share_pct=70.0,
        average_carbon_intensity=0.65,
        grid_energy_kwh=30.0,
        total_energy_kwh=100.0,
    )
    assert 0.0 <= score <= 100.0


@pytest.mark.skipif(ORTOOLS_AVAILABLE, reason="This test targets the documented missing-dependency guard")
def test_missing_ortools_is_reported_cleanly(settings):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        service = OptimizationService(db, settings)
        with pytest.raises(OptimizationError, match="OR-Tools is required"):
            service.run(OperatorObjective.balanced)


def test_persisted_run_metrics_are_stable_without_recomputation(db_session):
    from app.models.optimization_run import OptimizationRun
    from app.services.optimization.optimizer import Metrics, get_run_metrics

    run = OptimizationRun(
        id="RUN-SNAPSHOT",
        mode="balanced",
        scenario="normal",
        baseline_peak_kw=100.0,
        optimized_peak_kw=90.0,
        baseline_cost=1000.0,
        optimized_cost=900.0,
        baseline_renewable_share_pct=40.0,
        optimized_renewable_share_pct=60.0,
        baseline_co2_kg=20.0,
        optimized_co2_kg=10.0,
        status="candidate",
    )
    db_session.add(run)
    db_session.commit()

    before, after = get_run_metrics(db_session, None, run)
    assert isinstance(before, Metrics)
    assert before.peak_kw == 100.0
    assert after.peak_kw == 90.0
    assert before.renewable_share_pct == 40.0
    assert after.renewable_share_pct == 60.0
    assert before.co2_kg == 20.0
    assert after.co2_kg == 10.0


def test_scenario_modifiers_change_one_base_dataset(settings):
    from app.services.optimization.optimizer import OptimizationService, SlotContext
    from app.schemas.enums import Scenario

    base = [SlotContext(
        timestamp=datetime(2026, 9, 12, 12, 0),
        base_load_kw=500.0,
        renewable_kw=200.0,
        grid_capacity_kw=2200.0,
        electricity_price=8.0,
        carbon_intensity=0.75,
    )]
    class DummyDB: pass
    service = OptimizationService(DummyDB(), settings)

    normal = service._apply_scenario(base, Scenario.normal)[0]
    high_demand = service._apply_scenario(base, Scenario.high_demand)[0]
    high_renewable = service._apply_scenario(base, Scenario.high_renewable)[0]
    low_renewable = service._apply_scenario(base, Scenario.low_renewable)[0]

    assert normal == base[0]
    assert high_demand.base_load_kw > base[0].base_load_kw
    assert high_demand.electricity_price > base[0].electricity_price
    assert high_renewable.renewable_kw > base[0].renewable_kw
    assert low_renewable.renewable_kw < base[0].renewable_kw
