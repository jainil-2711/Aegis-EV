import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.database import Base


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
