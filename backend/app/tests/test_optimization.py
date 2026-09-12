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
from app.services.optimization.optimizer import OptimizationError, OptimizationService

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
