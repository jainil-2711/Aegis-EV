import pytest

from app.auth import (
    DEMO_USERS,
    authenticate_user,
    decode_token,
    ensure_demo_users,
    issue_token,
    require_role,
)
from app.database import Base
from app.models.user import User


def test_demo_users_can_authenticate(db_session):
    ensure_demo_users(db_session)
    for demo in DEMO_USERS:
        user = authenticate_user(db_session, demo["email"], demo["password"])
        assert user is not None
        assert user.role == demo["role"]


def test_signed_token_round_trip(settings, db_session):
    ensure_demo_users(db_session)
    user = db_session.get(User, "USR-NET-01")
    assert user is not None
    token, expires = issue_token(user, settings)
    assert expires > 0
    principal = decode_token(token, settings)
    assert principal.user_id == user.id
    assert principal.role == "network_operator"


def test_wrong_password_rejected(db_session):
    ensure_demo_users(db_session)
    assert authenticate_user(db_session, "driver@aegis.local", "wrong") is None


def test_role_permissions_are_separated():
    from app.auth import Principal, ROLE_DRIVER, ROLE_GRID, ROLE_NETWORK

    grid = Principal("g", "g@aegis.local", "Grid", ROLE_GRID)
    network = Principal("n", "n@aegis.local", "Network", ROLE_NETWORK)
    driver = Principal("d", "d@aegis.local", "Driver", ROLE_DRIVER)

    assert grid.can({ROLE_GRID})
    assert not grid.can({ROLE_NETWORK, ROLE_DRIVER})
    assert network.can({ROLE_NETWORK})
    assert not network.can({ROLE_DRIVER})
    assert driver.can({ROLE_DRIVER})
    assert not driver.can({ROLE_GRID, ROLE_NETWORK})


def test_route_rbac_with_real_tokens(db_session, monkeypatch):
    from fastapi.testclient import TestClient

    from app import main
    from app.auth import get_current_principal
    from app.database import get_db

    ensure_demo_users(db_session)

    def override_get_db():
        yield db_session

    main.app.dependency_overrides[get_db] = override_get_db
    # Remove the normal all-role test override so this test exercises the
    # real signed-token dependency and route guards.
    main.app.dependency_overrides.pop(get_current_principal, None)

    with TestClient(main.app) as client:
        driver_user = db_session.query(User).filter(User.role == "ev_driver").first()
        network_user = db_session.query(User).filter(User.role == "network_operator").first()
        grid_user = db_session.query(User).filter(User.role == "grid_operator").first()
        assert driver_user and network_user and grid_user

        driver_token, _ = issue_token(driver_user)
        network_token, _ = issue_token(network_user)
        grid_token, _ = issue_token(grid_user)

        assert client.get("/api/network/status", headers={"Authorization": driver_token}).status_code == 403
        assert client.post("/api/grid/signals", json={
            "start_time": "2026-09-12T18:00:00",
            "end_time": "2026-09-12T20:00:00",
            "condition": "high_demand",
            "recommended_ev_load_kw": 300,
            "signal_operator": "lte",
            "renewable_availability": "low",
        }, headers={"Authorization": network_token}).status_code == 403
        assert client.get("/api/driver/session", headers={"Authorization": grid_token}).status_code == 403

    main.app.dependency_overrides.pop(get_db, None)
