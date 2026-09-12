"""
Aegis — App Configuration

SHARED file. Do not fork settings per-module — add new settings here.

Notes:
- DATABASE_URL defaults to a local SQLite file so any developer can run the
  API and tests with zero external setup. docker-compose.yml provisions a
  real PostgreSQL instance for the full team demo (architecture.md SS3) —
  set DATABASE_URL there to switch. This is a hackathon-speed simplification
  (rules.md SS29 "Working > complete"); it does not change the fact that
  PostgreSQL is the chosen production-shaped database.
- SEED is the fixed random seed for deterministic synthetic data
  (data-spec.md SS16 / PRD.md SS11).
"""

import os
from functools import lru_cache
from pathlib import Path


class Settings:
    # --- Database -----------------------------------------------------
    # Resolve the local SQLite default relative to the backend package, not
    # the caller's current working directory. This prevents `seed_demo.py`
    # from the repo root and Uvicorn from `backend/` accidentally using
    # different databases.
    _backend_dir = Path(__file__).resolve().parent.parent
    _default_sqlite = (_backend_dir / "aegis.db").as_posix()
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{_default_sqlite}"
    )

    # --- Demo / simulation ---------------------------------------------
    seed: int = int(os.getenv("AEGIS_SEED", "42"))
    timezone: str = os.getenv("AEGIS_TIMEZONE", "Asia/Kolkata")

    # Fixed synthetic-day anchor. All EnergySlot timestamps and EV
    # arrival/departure times are generated relative to this date, so the
    # dataset is reproducible regardless of when seed_demo.py is actually
    # run (data-spec.md SS16).
    demo_day: str = os.getenv("AEGIS_DEMO_DAY", "2026-09-12")

    # Dataset sizing (PRD.md SS11 target demo dataset)
    num_evs: int = int(os.getenv("AEGIS_NUM_EVS", "40"))
    num_stations: int = int(os.getenv("AEGIS_NUM_STATIONS", "6"))
    num_chargers: int = int(os.getenv("AEGIS_NUM_CHARGERS", "24"))
    slot_minutes: int = int(os.getenv("AEGIS_SLOT_MINUTES", "30"))
    horizon_hours: int = int(os.getenv("AEGIS_HORIZON_HOURS", "24"))

    # --- Authentication ------------------------------------------------
    auth_secret: str = os.getenv("AEGIS_AUTH_SECRET", "aegis-local-demo-secret-change-me")
    auth_token_hours: int = int(os.getenv("AEGIS_AUTH_TOKEN_HOURS", "8"))

    # --- CORS (frontend dev server) ------------------------------------
    cors_origins: list[str] = os.getenv(
        "AEGIS_CORS_ORIGINS", "http://localhost:5173"
    ).split(",")


@lru_cache
def get_settings() -> Settings:
    return Settings()
