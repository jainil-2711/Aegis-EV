"""Integrated charging-network operator tests (P4)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.data.synthetic.generator import generate_full_dataset
from app.database import Base, get_db
from app.main import app
from app.models.charger import Charger
from app.models.energy_slot import EnergySlot
from app.models.ev import EV
from app.models.station import Station


@pytest.fixture()
def client():
    from app import models  # noqa: F401

    settings = Settings()
    settings.seed = 42
    settings.demo_day = "2026-09-12"
    settings.num_evs = 40
    settings.num_stations = 6
    settings.num_chargers = 24
    settings.slot_minutes = 30
    settings.horizon_hours = 24

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    dataset = generate_full_dataset(settings)
    db.bulk_insert_mappings(Station, dataset.stations)
    db.bulk_insert_mappings(Charger, dataset.chargers)
    db.bulk_insert_mappings(EV, dataset.evs)
    db.bulk_insert_mappings(EnergySlot, dataset.energy_slots)
    db.commit()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_stations_and_chargers_return_seeded_data(client):
    stations = client.get("/api/stations")
    assert stations.status_code == 200
    station_rows = stations.json()["stations"]
    assert len(station_rows) == 6

    chargers = client.get("/api/chargers")
    assert chargers.status_code == 200
    charger_rows = chargers.json()["chargers"]
    assert len(charger_rows) == 24
    station_ids = {s["id"] for s in station_rows}
    assert all(c["station_id"] in station_ids for c in charger_rows)


def test_network_ev_load_matches_grid_ev_load(client):
    network = client.get("/api/network/status")
    grid = client.get("/api/grid/status")
    assert network.status_code == 200
    assert grid.status_code == 200
    assert network.json()["ev_load"] == grid.json()["ev_load"]


def test_network_impact_requires_run(client):
    res = client.get("/api/network/impact")
    assert res.status_code == 409
    assert res.json()["detail"]["error"]["code"] == "NO_ACTIVE_SCHEDULE"


def test_network_impact_after_apply(client):
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration")
    run = client.post("/api/optimization/run", json={"mode": "cheapest"})
    assert run.status_code == 200
    run_id = run.json()["id"]

    applied = client.post(
        "/api/optimization/apply", json={"optimization_run_id": run_id}
    )
    assert applied.status_code == 200

    impact = client.get("/api/network/impact")
    assert impact.status_code == 200
    body = impact.json()
    assert body["active_optimization_run_id"] == run_id
    assert body["pricing_rule"]["currency"] == "INR"
    assert body["pricing_rule"]["base_rate"] >= 0


def test_no_dedicated_pricing_endpoint(client):
    assert client.get("/api/pricing").status_code == 404


def test_network_impact_ignores_unapplied_candidate(client):
    """Network impact must mean ACTIVE, never a later unapplied candidate
    (P4 Task 1). Sequence: apply run A, create (but do not apply) run B,
    confirm impact still reports A — never B, and never a 200 built from B.
    """
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration")

    run_a = client.post("/api/optimization/run", json={"mode": "cheapest"})
    assert run_a.status_code == 200
    run_a_id = run_a.json()["id"]

    applied_a = client.post(
        "/api/optimization/apply", json={"optimization_run_id": run_a_id}
    )
    assert applied_a.status_code == 200

    impact_after_a = client.get("/api/network/impact")
    assert impact_after_a.status_code == 200
    assert impact_after_a.json()["active_optimization_run_id"] == run_a_id

    # Create a second candidate — deliberately do NOT apply it.
    run_b = client.post("/api/optimization/run", json={"mode": "greenest"})
    assert run_b.status_code == 200
    run_b_id = run_b.json()["id"]
    assert run_b_id != run_a_id

    impact_still_a = client.get("/api/network/impact")
    assert impact_still_a.status_code == 200
    assert impact_still_a.json()["active_optimization_run_id"] == run_a_id, (
        "Network impact must not follow an unapplied candidate"
    )

    # Now apply B and confirm impact moves to B (proves apply, not creation,
    # is what changes the active schedule).
    applied_b = client.post(
        "/api/optimization/apply", json={"optimization_run_id": run_b_id}
    )
    assert applied_b.status_code == 200

    impact_after_b = client.get("/api/network/impact")
    assert impact_after_b.status_code == 200
    assert impact_after_b.json()["active_optimization_run_id"] == run_b_id
