"""Charger model — data-spec.md SS6. Written by P1's synthetic generator."""

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Charger(Base):
    __tablename__ = "chargers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id"))
    max_power_kw: Mapped[float] = mapped_column(Float)
    connector_type: Mapped[str] = mapped_column(String)  # ConnectorType
    status: Mapped[str] = mapped_column(String)  # ChargerStatus
