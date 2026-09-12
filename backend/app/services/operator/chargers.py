"""
GreenCharge — Operator: Chargers Service (P4)

Owns:
    GET /api/chargers

Contract: schemas.ChargersResponse (api-contract.md SS4, data-spec.md SS6).

--------------------------------------------------------------------------
INTEGRATION ADAPTER — CONFIRM AGAINST P1's REAL CODE
--------------------------------------------------------------------------
Assumes a SQLAlchemy `Charger` model seeded by P1. Charger assignment
to EVs is fixed at seed time (data-spec.md SS3) — this module only
reads status/power/connector info, it never reassigns a charger.
"""

from sqlalchemy.orm import Session

# ADAPTER: adjust if P1's real model path differs.
from app.models.charger import Charger

from app.schemas.operator import ChargersResponse
from app.schemas.operator import ChargerSummary


def get_chargers(db: Session, station_id: str | None = None) -> ChargersResponse:
    query = db.query(Charger)
    if station_id is not None:
        query = query.filter(Charger.station_id == station_id)
    chargers = query.all()

    return ChargersResponse(
        chargers=[
            ChargerSummary(
                id=c.id,
                station_id=c.station_id,
                max_power_kw=c.max_power_kw,
                connector_type=c.connector_type,
                status=c.status,
            )
            for c in chargers
        ]
    )
