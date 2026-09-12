import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.database import Base
from app.auth import Principal, get_current_principal
from app.main import app


@pytest.fixture()
def settings() -> Settings:
    s = Settings()
    s.seed = 42
    s.demo_day = "2026-09-12"
    s.num_evs = 40
    s.num_stations = 6
    s.num_chargers = 24
    s.slot_minutes = 30
    s.horizon_hours = 24
    return s


@pytest.fixture()
def db_session():
    # Fresh in-memory SQLite per test — isolated from any real dev DB file.
    from app import models  # noqa: F401 register models on Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def auth_override():
    """Tests use an explicit all-role test principal; production enforces RBAC."""
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        user_id="TEST-USER",
        email="test@aegis.local",
        display_name="Test User",
        role="test",
        roles=frozenset({"grid_operator", "network_operator", "ev_driver"}),
    )
    yield
    app.dependency_overrides.pop(get_current_principal, None)
