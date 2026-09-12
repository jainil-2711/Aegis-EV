import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data.synthetic.generator import generate_full_dataset
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(settings):
    from app import models  # noqa: F401

    # StaticPool: TestClient may dispatch requests on a different thread
    # than this fixture; a plain ":memory:" DB is per-connection, so
    # without a shared static connection the app would see an empty DB.
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

    # Seed via the generator directly (bypasses scripts/seed_demo.py's own
    # engine so this test doesn't touch a real DB file).
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

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_grid_status_shape(client):
    resp = client.get("/api/grid/status")
    assert resp.status_code == 200
    body = resp.json()
    for key in (
        "grid_demand_kw",
        "grid_capacity_kw",
        "renewable_generation_kw",
        "ev_load",
        "headroom_kw",
    ):
        assert key in body
    for key in ("current_ev_load_kw", "scheduled_ev_load_kw", "peak_ev_load_kw"):
        assert key in body["ev_load"]


def test_grid_forecast_returns_all_slots(client, settings):
    resp = client.get("/api/grid/forecast")
    assert resp.status_code == 200
    slots = resp.json()["slots"]
    assert len(slots) == settings.horizon_hours * 60 / settings.slot_minutes


def test_grid_signal_create_and_list(client):
    payload = {
        "start_time": "2026-09-12T18:00:00",
        "end_time": "2026-09-12T20:00:00",
        "condition": "high_demand",
        "recommended_ev_load_kw": 300,
        "signal_operator": "lte",
        "renewable_availability": "low",
    }
    create_resp = client.post("/api/grid/signals", json=payload)
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["condition"] == "high_demand"
    assert "id" in created and "created_at" in created

    list_resp = client.get("/api/grid/signals")
    assert list_resp.status_code == 200
    signals = list_resp.json()["signals"]
    assert len(signals) == 1
    assert signals[0]["id"] == created["id"]


def test_grid_ev_load_endpoint(client):
    resp = client.get("/api/grid/ev-load")
    assert resp.status_code == 200
    body = resp.json()["ev_load"]
    for key in ("current_ev_load_kw", "scheduled_ev_load_kw", "peak_ev_load_kw"):
        assert key in body
