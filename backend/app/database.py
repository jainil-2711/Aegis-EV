"""
Aegis — Database wiring (SHARED)

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
    _apply_additive_column_migrations()


def _apply_additive_column_migrations() -> None:
    """Add newly introduced nullable columns to tables that already existed
    on disk from before the model change (hackathon-speed stand-in for a
    real Alembic migration).

    `Base.metadata.create_all()` only creates *missing tables*; it never
    alters an existing table's columns. Without this, a pre-existing local
    dev/demo SQLite (or Postgres) database predating a column addition would
    make every startup crash with "no such column" instead of picking up
    the new column automatically. Only ever adds columns — never drops or
    renames anything, so existing data is untouched.
    """
    from sqlalchemy import inspect, text
    from sqlalchemy.exc import OperationalError, ProgrammingError

    # (table_name, column_name, column_type_ddl)
    additive_columns = [
        ("evs", "owner_user_id", "VARCHAR"),
    ]

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table_name, column_name, column_type_ddl in additive_columns:
        if table_name not in existing_tables:
            continue
        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
        if column_name in existing_columns:
            continue
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_ddl}")
                )
        except (OperationalError, ProgrammingError):
            # Another worker/process already added it concurrently, or the
            # dialect rejected it for a reason create_all() will surface
            # anyway on first real use — don't block app startup on this
            # best-effort self-heal.
            pass