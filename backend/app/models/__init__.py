"""
Aegis — SQLAlchemy models (SHARED)

Importing this package registers every mapped class on `Base.metadata`, so
`database.create_all_tables()` can create every table in one call.

Ownership (coordinate before changing — rules.md SS13, SS14):
    ev.py, station.py, charger.py, energy_slot.py, grid_signal.py  -> P1
    optimization_run.py, charging_schedule_entry.py                -> P2
    charging_session.py                                            -> P3
(operator.py has no dedicated model; P4 reads station/charger/ev_load)
"""

from app.models.charger import Charger
from app.models.charging_schedule_entry import ChargingScheduleEntry
from app.models.charging_session import ChargingSession
from app.models.energy_slot import EnergySlot
from app.models.ev import EV
from app.models.grid_signal import GridSignal
from app.models.optimization_run import OptimizationRun
from app.models.station import Station
from app.models.user import User

__all__ = [
    "Charger",
    "ChargingScheduleEntry",
    "ChargingSession",
    "EnergySlot",
    "EV",
    "GridSignal",
    "OptimizationRun",
    "Station",
    "User",
]
