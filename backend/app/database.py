"""
GreenCharge — Database wiring (SHARED)

One engine, one session factory, one declarative Base, used by every
module's models/ and services/. Do not create a second engine elsewhere
(architecture.md SS1 "one backend, one database").
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a request-scoped DB session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    """
    Create tables from metadata if they don't exist.

    Hackathon-speed simplification in place of Alembic migrations
    (rules.md SS13 still governs *shared* schema changes — coordinate before
    changing a model, this just skips migration-file bookkeeping for MVP
    speed). Safe to call repeatedly; it never drops or alters data.
    """
    # Importing the models package registers all mapped classes on Base
    # before create_all() runs.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
