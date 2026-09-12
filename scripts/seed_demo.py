"""Aegis demo seed script.

Recreates deterministic synthetic data and clears runtime demo state so each
run starts from a clean application state.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.auth import ensure_demo_users  # noqa: E402
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
        db.query(ChargingSession).delete()
        db.query(ChargingScheduleEntry).delete()
        db.query(OptimizationRun).delete()
        db.query(GridSignal).delete()
        db.query(EV).delete()
        db.query(Charger).delete()
        db.query(Station).delete()
        db.query(EnergySlot).delete()
        db.commit()

        db.bulk_insert_mappings(Station, dataset.stations)
        db.bulk_insert_mappings(Charger, dataset.chargers)
        db.bulk_insert_mappings(EV, dataset.evs)
        db.bulk_insert_mappings(EnergySlot, dataset.energy_slots)
        db.commit()
        ensure_demo_users(db)

        print(
            f"Seeded {len(dataset.stations)} stations, {len(dataset.chargers)} chargers, "
            f"{len(dataset.evs)} EVs, {len(dataset.energy_slots)} energy slots "
            f"(seed={settings.seed}, demo_day={settings.demo_day})."
        )
        print("Demo runtime state reset: runs=0, schedule_entries=0, sessions=0, grid_signals=0")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
