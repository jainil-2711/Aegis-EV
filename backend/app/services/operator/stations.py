"""
Aegis — Operator: Stations Service (P4)

Owns:
    GET /api/stations

Contract: schemas.StationsResponse (api-contract.md SS4, data-spec.md SS5).

--------------------------------------------------------------------------
INTEGRATION ADAPTER — CONFIRM AGAINST P1's REAL CODE
--------------------------------------------------------------------------
Assumes a SQLAlchemy `Station` model seeded by P1's scripts/seed_demo.py,
queryable read-only here. If P1's real model path differs, adjust only
the import line.
"""

from sqlalchemy.orm import Session

# ADAPTER: adjust if P1's real model path differs.
from app.models.station import Station

from app.schemas.operator import StationsResponse
from app.schemas.operator import StationSummary


def get_stations(db: Session) -> StationsResponse:
    stations = db.query(Station).all()
    return StationsResponse(
        stations=[
            StationSummary(
                id=s.id,
                name=s.name,
                capacity_kw=s.capacity_kw,
                charger_count=s.charger_count,
            )
            for s in stations
        ]
    )
