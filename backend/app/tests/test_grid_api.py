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

    # StaticPool is required because TestClient may execute the application
    # in another thread. A plain ":memory:" SQLite database is otherwise
    # connection-local.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed the test database from the deterministic synthetic generator.
    dataset = generate_full_dataset(settings)

    db = TestingSessionLocal()

    from app.models.charger import Charger
    from app.models.energy_slot import EnergySlot
    from app.models.ev import EV
    from app.models.station import Station

    db.bulk_insert_mappings(
        Station,
        dataset.stations,
    )

    db.bulk_insert_mappings(
        Charger,
        dataset.chargers,
    )

    db.bulk_insert_mappings(
        EV,
        dataset.evs,
    )

    db.bulk_insert_mappings(
        EnergySlot,
        dataset.energy_slots,
    )

    db.commit()
    db.close()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_health(client):
    resp = client.get("/api/health")

    assert resp.status_code == 200
    assert resp.json() == {
        "status": "ok"
    }


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
        "solar_generation_kw",
        "wind_generation_kw",
        "source_type",
    ):
        assert key in body

    for key in (
        "current_ev_load_kw",
        "scheduled_ev_load_kw",
        "peak_ev_load_kw",
    ):
        assert key in body["ev_load"]


def test_grid_status_renewable_relationship(client):
    """
    P1 invariant:

        renewable_generation_kw
            =
        solar_generation_kw + wind_generation_kw
    """

    resp = client.get("/api/grid/status")

    assert resp.status_code == 200

    body = resp.json()

    solar = body["solar_generation_kw"]
    wind = body["wind_generation_kw"]
    renewable = body["renewable_generation_kw"]

    assert solar >= 0.0
    assert wind >= 0.0
    assert renewable >= 0.0

    assert renewable == solar + wind


def test_grid_status_demand_relationship(client):
    """
    P1 grid-demand invariant:

        grid_demand_kw
            =
        base_load_kw + current_ev_load_kw
    """

    resp = client.get("/api/grid/status")

    assert resp.status_code == 200

    body = resp.json()

    base_load = body["base_load_kw"]
    current_ev_load = body["ev_load"][
        "current_ev_load_kw"
    ]
    grid_demand = body["grid_demand_kw"]

    assert base_load >= 0.0
    assert current_ev_load >= 0.0

    assert grid_demand == pytest.approx(
        base_load + current_ev_load,
        abs=0.1,
    )


def test_grid_status_headroom_relationship(client):
    """
    P1 grid-headroom invariant:

        headroom_kw
            =
        grid_capacity_kw - grid_demand_kw
    """

    resp = client.get("/api/grid/status")

    assert resp.status_code == 200

    body = resp.json()

    capacity = body["grid_capacity_kw"]
    demand = body["grid_demand_kw"]
    headroom = body["headroom_kw"]

    assert capacity >= 0.0

    assert headroom == (
        capacity
        - demand
    )


def test_grid_forecast_returns_all_slots(client, settings):
    resp = client.get("/api/grid/forecast")

    assert resp.status_code == 200

    slots = resp.json()["slots"]

    assert len(slots) == (
        settings.horizon_hours
        * 60
        / settings.slot_minutes
    )


def test_grid_forecast_contains_separate_renewables(
    client,
):
    resp = client.get("/api/grid/forecast")

    assert resp.status_code == 200

    slots = resp.json()["slots"]

    assert len(slots) > 0

    for slot in slots:
        assert "solar_generation_kw" in slot
        assert "wind_generation_kw" in slot
        assert "renewable_kw" in slot

        assert slot["solar_generation_kw"] >= 0.0
        assert slot["wind_generation_kw"] >= 0.0
        assert slot["renewable_kw"] >= 0.0

        assert slot["renewable_kw"] == (
            slot["solar_generation_kw"]
            + slot["wind_generation_kw"]
        )


def test_grid_forecast_source_metadata(client):
    resp = client.get("/api/grid/forecast")

    assert resp.status_code == 200

    slots = resp.json()["slots"]

    for slot in slots:
        assert "source_type" in slot
        assert slot["source_type"] == "synthetic"

        assert "forecast_for" in slot
        assert slot["forecast_for"] is not None


def test_grid_signal_create_and_list(client):
    payload = {
        "start_time": "2026-09-12T18:00:00",
        "end_time": "2026-09-12T20:00:00",
        "condition": "high_demand",
        "recommended_ev_load_kw": 300,
        "signal_operator": "lte",
        "renewable_availability": "low",
    }

    create_resp = client.post(
        "/api/grid/signals",
        json=payload,
    )

    assert create_resp.status_code == 201

    created = create_resp.json()

    assert created["condition"] == "high_demand"
    assert "id" in created
    assert "created_at" in created

    list_resp = client.get(
        "/api/grid/signals"
    )

    assert list_resp.status_code == 200

    signals = list_resp.json()["signals"]

    assert len(signals) == 1
    assert signals[0]["id"] == created["id"]


def test_grid_ev_load_endpoint(client):
    resp = client.get(
        "/api/grid/ev-load"
    )

    assert resp.status_code == 200

    body = resp.json()["ev_load"]

    for key in (
        "current_ev_load_kw",
        "scheduled_ev_load_kw",
        "peak_ev_load_kw",
    ):
        assert key in body