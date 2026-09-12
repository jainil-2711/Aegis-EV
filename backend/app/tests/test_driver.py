"""Driver API tests (P3), integrated with the real P1/P2 repository."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.data.synthetic.generator import generate_full_dataset
from app.database import Base, get_db
from app.main import app
from app.models.charger import Charger
from app.models.energy_slot import EnergySlot
from app.models.ev import EV
from app.models.station import Station

# The autouse `auth_override` fixture in conftest.py replaces the real auth
# dependency with a fixed Principal(user_id="TEST-USER", ...). P3's EV
# ownership check requires an explicit owner_user_id, so the fixture below
# binds that same id to the seeded demo EV to keep these tests behaving
# exactly as before ownership enforcement was added.
TEST_PRINCIPAL_USER_ID = "TEST-USER"


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
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    dataset = generate_full_dataset(settings)
    db.bulk_insert_mappings(Station, dataset.stations)
    db.bulk_insert_mappings(Charger, dataset.chargers)
    db.bulk_insert_mappings(EV, dataset.evs)
    db.bulk_insert_mappings(EnergySlot, dataset.energy_slots)
    db.commit()

    # Bind the demo test principal to EV-101 (P3 server-side ownership).
    demo_ev = db.get(EV, "EV-101")
    demo_ev.owner_user_id = TEST_PRINCIPAL_USER_ID
    db.add(demo_ev)
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_get_driver_session_returns_seeded_ev(client):
    res = client.get("/api/driver/session")
    assert res.status_code == 200
    body = res.json()
    assert body["ev_id"] == "EV-101"
    assert 0 <= body["current_soc"] <= 100
    assert body["flexibility"] in ("high", "medium", "low", "non_flexible")


def test_driver_preferences_update_preserves_canonical_flexibility(client):
    before = client.get("/api/driver/session").json()
    target = min(100.0, before["current_soc"] + 10.0)
    res = client.post(
        "/api/driver/preferences",
        json={"preference": "greenest", "target_soc": target},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["preference"] == "greenest"
    assert body["target_soc"] == target
    assert body["flexibility"] in ("high", "medium", "low", "non_flexible")


def test_infeasible_override_returns_alternatives_not_silent_failure(client):
    res = client.post(
        "/api/driver/schedule/override",
        json={"requested_power_kw": 999999.0, "reason": "unrealistic power"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["feasible"] is False
    assert body["explanation"]
    assert body["alternatives"]


def test_override_response_has_no_punitive_fields(client):
    res = client.post(
        "/api/driver/schedule/override",
        json={"requested_power_kw": 7.0, "reason": "testing"},
    )
    assert res.status_code == 200
    forbidden = {"price_penalty", "fine", "access_level", "punitive"}
    assert forbidden.isdisjoint(res.json().keys())


def test_accept_records_run_id_and_updates_status(client):
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration tests")
    run_res = client.post("/api/optimization/run", json={"mode": "balanced"})
    assert run_res.status_code in (200, 201)
    run_id = run_res.json()["id"]

    apply_res = client.post(
        "/api/optimization/apply",
        json={"optimization_run_id": run_id},
    )
    assert apply_res.status_code == 200

    accept_res = client.post(
        "/api/driver/schedule/accept",
        json={"optimization_run_id": run_id},
    )
    assert accept_res.status_code == 200
    body = accept_res.json()
    assert body["accepted"] is True
    assert body["status"] == "scheduled"


def test_driver_cannot_accept_candidate_before_network_operator_applies_it(client):
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration tests")
    run_res = client.post("/api/optimization/run", json={"mode": "balanced"})
    assert run_res.status_code == 200
    run_id = run_res.json()["id"]

    accept_res = client.post(
        "/api/driver/schedule/accept",
        json={"optimization_run_id": run_id},
    )
    assert accept_res.status_code == 409
    assert accept_res.json()["detail"]["error"]["code"] == "INVALID_SESSION_ACTION"



def test_recommendation_requires_active_schedule_and_matches_active_run(client):
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration tests")
    run_res = client.post("/api/optimization/run", json={"mode": "greenest"})
    assert run_res.status_code == 200
    run_body = run_res.json()

    ev_entries = [e for e in run_body["schedule"] if e["ev_id"] == "EV-101"]
    assert ev_entries

    before_apply = client.get("/api/driver/recommendation")
    assert before_apply.status_code == 409
    assert before_apply.json()["detail"]["error"]["code"] == "NO_ACTIVE_SCHEDULE"

    apply_res = client.post(
        "/api/optimization/apply",
        json={"optimization_run_id": run_body["id"]},
    )
    assert apply_res.status_code == 200

    rec_res = client.get("/api/driver/recommendation")
    assert rec_res.status_code == 200
    rec = rec_res.json()

    assert rec["optimization_run_id"] == run_body["id"]
    assert rec["estimated_cost"] == pytest.approx(
        sum(e["cost"] for e in ev_entries), abs=0.05
    )
    assert rec["co2_impact_kg"] == pytest.approx(
        sum(e["co2_kg"] for e in ev_entries), abs=0.05
    )


def test_driver_recommendation_uses_active_run_not_latest_candidate(client):
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration tests")
    first = client.post("/api/optimization/run", json={"mode": "cheapest"})
    assert first.status_code == 200
    first_id = first.json()["id"]
    assert client.post("/api/optimization/apply", json={"optimization_run_id": first_id}).status_code == 200

    second = client.post("/api/optimization/run", json={"mode": "greenest"})
    assert second.status_code == 200
    second_id = second.json()["id"]
    assert second_id != first_id

    rec = client.get("/api/driver/recommendation")
    assert rec.status_code == 200
    assert rec.json()["optimization_run_id"] == first_id



def test_status_uses_demo_clock_when_active_schedule_exists(client):
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration tests")
    run_res = client.post("/api/optimization/run", json={"mode": "balanced"})
    assert run_res.status_code == 200
    run_id = run_res.json()["id"]
    apply_res = client.post(
        "/api/optimization/apply",
        json={"optimization_run_id": run_id},
    )
    assert apply_res.status_code == 200

    accept_res = client.post(
        "/api/driver/schedule/accept",
        json={"optimization_run_id": run_id},
    )
    assert accept_res.status_code == 200

    status_res = client.get("/api/driver/session/status")
    assert status_res.status_code == 200
    body = status_res.json()
    assert body["simulated"] is True
    # Response must expose the fixed demo day, not an arbitrary wall-clock date.
    assert body["updated_at"].startswith("2026-09-12")


def test_simulated_live_status_transitions_from_scheduled_to_charging_to_completed(client, monkeypatch):
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration tests")
    run_res = client.post("/api/optimization/run", json={"mode": "balanced"})
    assert run_res.status_code == 200
    run_id = run_res.json()["id"]

    assert client.post("/api/optimization/apply", json={"optimization_run_id": run_id}).status_code == 200
    assert client.post("/api/driver/schedule/accept", json={"optimization_run_id": run_id}).status_code == 200

    recommendation = client.get("/api/driver/recommendation").json()
    start = datetime.fromisoformat(recommendation["window_start"])
    end = datetime.fromisoformat(recommendation["window_end"])

    import app.services.driver.status as status_service

    monkeypatch.setattr(status_service, "current_demo_timestamp", lambda settings, now=None: start - timedelta(minutes=1))
    scheduled = client.get("/api/driver/session/status").json()
    assert scheduled["status"] == "scheduled"
    assert scheduled["charging_power_kw"] == 0

    monkeypatch.setattr(status_service, "current_demo_timestamp", lambda settings, now=None: start + timedelta(minutes=1))
    charging = client.get("/api/driver/session/status").json()
    assert charging["status"] == "charging"
    assert charging["current_soc"] > 0
    assert charging["charging_power_kw"] > 0

    monkeypatch.setattr(status_service, "current_demo_timestamp", lambda settings, now=None: end + timedelta(minutes=1))
    completed = client.get("/api/driver/session/status").json()
    assert completed["status"] == "completed"
    assert completed["current_soc"] > 0


# ---------------------------------------------------------------------------
# P3 Task 2 / Task 6 — server-side EV ownership authorization
#
# These tests bypass the conftest.py `auth_override` fixture (all-role test
# principal) so they exercise the *real* signed-token auth dependency and
# the real EV ownership check, matching how the frontend and a real driver
# actually authenticate.
# ---------------------------------------------------------------------------


@pytest.fixture()
def real_auth_client():
    """Same dataset as `client`, but with real login/token auth enabled."""
    from app import models  # noqa: F401
    from app.auth import ensure_demo_users, get_current_principal, issue_token

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
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    dataset = generate_full_dataset(settings)
    db.bulk_insert_mappings(Station, dataset.stations)
    db.bulk_insert_mappings(Charger, dataset.chargers)
    db.bulk_insert_mappings(EV, dataset.evs)
    db.bulk_insert_mappings(EnergySlot, dataset.energy_slots)
    db.commit()

    # Creates demo users AND binds the demo driver -> EV-101 (see app.auth).
    ensure_demo_users(db)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # This is the important difference from `client`: do NOT override
    # get_current_principal, so real signed tokens and RBAC are exercised.
    app.dependency_overrides.pop(get_current_principal, None)

    from app.models.user import User

    driver_user = db.query(User).filter(User.role == "ev_driver").first()
    grid_user = db.query(User).filter(User.role == "grid_operator").first()
    driver_token, _ = issue_token(driver_user)
    grid_token, _ = issue_token(grid_user)

    try:
        with TestClient(app) as test_client:
            yield test_client, db, driver_token, grid_token
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def test_driver_can_access_own_ev(real_auth_client):
    test_client, _db, driver_token, _grid_token = real_auth_client

    res = test_client.get("/api/driver/session", headers={"Authorization": driver_token})
    assert res.status_code == 200
    assert res.json()["ev_id"] == "EV-101"

    res_explicit = test_client.get(
        "/api/driver/session", params={"ev_id": "EV-101"}, headers={"Authorization": driver_token}
    )
    assert res_explicit.status_code == 200
    assert res_explicit.json()["ev_id"] == "EV-101"


def test_driver_cannot_access_another_evs_data(real_auth_client):
    test_client, _db, driver_token, _grid_token = real_auth_client

    res = test_client.get(
        "/api/driver/session", params={"ev_id": "EV-102"}, headers={"Authorization": driver_token}
    )
    assert res.status_code == 403
    assert res.json()["detail"]["error"]["code"] == "EV_NOT_AUTHORIZED"


def test_driver_endpoints_require_a_token(real_auth_client):
    test_client, _db, _driver_token, _grid_token = real_auth_client

    res = test_client.get("/api/driver/session")
    assert res.status_code == 401


def test_driver_endpoints_reject_wrong_role(real_auth_client):
    test_client, _db, _driver_token, grid_token = real_auth_client

    res = test_client.get("/api/driver/session", headers={"Authorization": grid_token})
    assert res.status_code == 403


def test_driver_cannot_accept_or_override_another_evs_schedule(real_auth_client):
    pytest.importorskip("ortools", reason="OR-Tools required for optimizer integration tests")
    test_client, _db, driver_token, _grid_token = real_auth_client

    override_res = test_client.post(
        "/api/driver/schedule/override",
        params={"ev_id": "EV-102"},
        json={"requested_power_kw": 7.0, "reason": "testing"},
        headers={"Authorization": driver_token},
    )
    assert override_res.status_code == 403
    assert override_res.json()["detail"]["error"]["code"] == "EV_NOT_AUTHORIZED"

    accept_res = test_client.post(
        "/api/driver/schedule/accept",
        params={"ev_id": "EV-102"},
        json={"optimization_run_id": "does-not-matter"},
        headers={"Authorization": driver_token},
    )
    assert accept_res.status_code == 403
    assert accept_res.json()["detail"]["error"]["code"] == "EV_NOT_AUTHORIZED"