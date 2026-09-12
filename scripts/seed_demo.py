"""
GreenCharge — Demo Seed Script

Creates a deterministic synthetic GreenCharge demo dataset and resets
runtime/demo state so each seed starts from a clean application state.

Cleared runtime/demo state:
    - charging_sessions
    - charging_schedule_entries
    - optimization_runs
    - grid_signals

Cleared synthetic data:
    - evs
    - chargers
    - stations
    - energy_slots

Usage:
    From repo root:
        python scripts/seed_demo.py

    From backend:
        python ..scripts/seed_demo.py
"""

import sys
from pathlib import Path


# Allow running as `python scripts/seed_demo.py` from repo root.
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "backend"),
)

from app.config import get_settings  # noqa: E402
from app.data.synthetic.generator import generate_full_dataset  # noqa: E402
from app.database import SessionLocal, create_all_tables  # noqa: E402
from app.models.charger import Charger  # noqa: E402
from app.models.charging_schedule_entry import ChargingScheduleEntry  # noqa: E402
from app.models.charging_session import ChargingSession  # noqa: E402
from app.models.energy_slot import EnergySlot  # noqa: E402
from app.models.ev import EV  # noqa: E402
from app.models.grid_signal import GridSignal  # noqa: E402
from app.models.optimization_run import OptimizationRun  # noqa: E402
from app.models.station import Station  # noqa: E402


def seed() -> None:
    settings = get_settings()
    create_all_tables()

    dataset = generate_full_dataset(settings)

    db = SessionLocal()

    try:
        # ------------------------------------------------------------
        # 1. Clear runtime/demo state in foreign-key dependency order.
        # ------------------------------------------------------------
        #
        # ChargingSession -> OptimizationRun
        # ChargingScheduleEntry -> OptimizationRun
        #
        # Therefore both child tables must be cleared before
        # OptimizationRun.
        db.query(ChargingSession).delete()
        db.query(ChargingScheduleEntry).delete()
        db.query(OptimizationRun).delete()

        # Grid signals are independent of the optimization run, but
        # clearing them keeps the Grid Operator screen fully fresh.
        db.query(GridSignal).delete()

        # ------------------------------------------------------------
        # 2. Clear synthetic P1 data.
        # ------------------------------------------------------------
        #
        # EV -> Charger -> Station
        # so delete in reverse dependency order.
        db.query(EV).delete()
        db.query(Charger).delete()
        db.query(Station).delete()
        db.query(EnergySlot).delete()

        db.commit()

        # ------------------------------------------------------------
        # 3. Insert fresh deterministic synthetic data.
        # ------------------------------------------------------------
        db.bulk_insert_mappings(Station, dataset.stations)
        db.bulk_insert_mappings(Charger, dataset.chargers)
        db.bulk_insert_mappings(EV, dataset.evs)
        db.bulk_insert_mappings(EnergySlot, dataset.energy_slots)

        db.commit()

        print(
            f"Seeded {len(dataset.stations)} stations, "
            f"{len(dataset.chargers)} chargers, "
            f"{len(dataset.evs)} EVs, "
            f"{len(dataset.energy_slots)} energy slots "
            f"(seed={settings.seed}, demo_day={settings.demo_day})."
        )

        print("Demo runtime state reset:")
        print("  optimization_runs = 0")
        print("  charging_schedule_entries = 0")
        print("  charging_sessions = 0")
        print("  grid_signals = 0")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()