"""
GreenCharge — Shared Enums (SHARED, frozen contract)

Copied verbatim from the project's schemas.py. Do not add/rename/remove
values without updating schemas.py, api.ts, api-contract.md, and
CHANGELOG.md in the same PR (rules.md SS12).
"""

from enum import Enum


class SignalOperator(str, Enum):
    lte = "lte"
    gte = "gte"


class GridCondition(str, Enum):
    normal = "normal"
    high_demand = "high_demand"
    high_renewable = "high_renewable"
    low_renewable = "low_renewable"


class RenewableAvailability(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ConnectorType(str, Enum):
    type2 = "type2"
    ccs = "ccs"
    chademo = "chademo"
    other = "other"


class ChargerStatus(str, Enum):
    available = "available"
    occupied = "occupied"
    offline = "offline"
    maintenance = "maintenance"


class SessionStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    charging = "charging"
    completed = "completed"
    cancelled = "cancelled"


class DriverPreference(str, Enum):
    cheapest = "cheapest"
    greenest = "greenest"
    balanced = "balanced"
    immediate = "immediate"


class OperatorObjective(str, Enum):
    cheapest = "cheapest"
    greenest = "greenest"
    balanced = "balanced"


class Flexibility(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    non_flexible = "non_flexible"


class OptimizationStatus(str, Enum):
    pending = "pending"
    candidate = "candidate"
    applied = "applied"
    superseded = "superseded"
    rejected = "rejected"


class DataSource(str, Enum):
    synthetic = "synthetic"
    external = "external"
    derived = "derived"


class Scenario(str, Enum):
    normal = "normal"
    high_demand = "high_demand"
    high_renewable = "high_renewable"
    low_renewable = "low_renewable"
