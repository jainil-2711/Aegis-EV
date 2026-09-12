"""
GreenCharge — Simulation Clock (SHARED helper)

The demo dataset lives on one fixed day (`settings.demo_day`). "Current
time" for the demo is real wall-clock time-of-day mapped onto that fixed
day, so the Grid/Operator/Driver views always show a plausible, moving
"now" without needing the demo to literally run across 24 real hours.

This is intentionally simple and documented as a demo convenience — it is
not a claim about live grid telemetry (design.md SS13, PRD.md SS13).
"""

from datetime import datetime, timedelta

from app.config import Settings


def current_demo_timestamp(settings: Settings, now: datetime | None = None) -> datetime:
    """
    Map the real current time-of-day onto settings.demo_day, snapped to the
    nearest slot boundary. `now` is injectable for tests.
    """
    now = now or datetime.now()
    demo_day = datetime.fromisoformat(settings.demo_day)

    seconds_into_day = now.hour * 3600 + now.minute * 60 + now.second
    slot_seconds = settings.slot_minutes * 60
    snapped_seconds = (seconds_into_day // slot_seconds) * slot_seconds

    return demo_day + timedelta(seconds=snapped_seconds)


def current_slot_index(settings: Settings, now: datetime | None = None) -> int:
    ts = current_demo_timestamp(settings, now)
    demo_day = datetime.fromisoformat(settings.demo_day)
    minutes_elapsed = (ts - demo_day).total_seconds() / 60.0
    return int(minutes_elapsed // settings.slot_minutes)
