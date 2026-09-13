"""
Aegis — Simulation Clock (SHARED helper)

The demo dataset lives on one fixed day (`settings.demo_day`). "Current
time" for the demo is real wall-clock time-of-day mapped onto that fixed
day, so the Grid/Operator/Driver views always show a plausible, moving
"now" without needing the demo to literally run across 24 real hours.

This is intentionally simple and documented as a demo convenience — it is
not a claim about live grid telemetry (design.md SS13, PRD.md SS13).

--- CHANGE (see PR notes) ---------------------------------------------
Default behavior is byte-for-byte unchanged: with no env var set, "now"
is still exactly `now.hour:now.minute:now.second` mapped onto demo_day,
same as before.

Problem this fixes: a live demo in front of a mentor almost never happens
to fall inside the seeded charging window (e.g. 2:00–5:00 PM), so
charging_power_kw / cost_so_far / co2_so_far / green_score sit at 0 for
the entire meeting with no way to show progress on demand.

Fix: an opt-in wall-clock multiplier, set via
    AEGIS_DEMO_CLOCK_SPEED=<float>
(e.g. 60 = one real minute becomes one simulated hour). When unset (or
set to 1), nothing changes. When set, the simulated time-of-day starts
at whatever real time-of-day the backend process booted at, then runs
forward `speed`x faster than real time, wrapping every 24 simulated
hours. This lets a 3-hour charging window play out in a few minutes
without touching demo_day, seed data, or any other file.
-------------------------------------------------------------------------
"""

import os
from datetime import datetime, timedelta

from app.config import Settings

SECONDS_PER_DAY = 24 * 3600

# Anchor point: the instant this process started, and the real
# time-of-day it started at. Used only when acceleration is enabled.
_PROCESS_START = datetime.now()
_PROCESS_START_SECONDS_INTO_DAY = (
    _PROCESS_START.hour * 3600 + _PROCESS_START.minute * 60 + _PROCESS_START.second
)


def _demo_clock_speed() -> float:
    """Read AEGIS_DEMO_CLOCK_SPEED fresh on every call so it can be tuned
    without a restart-sensitive cache. Falls back to 1.0 (unchanged
    real-time behavior) on anything unparsable or unset."""
    raw = os.environ.get("AEGIS_DEMO_CLOCK_SPEED", "1")
    try:
        speed = float(raw)
    except (TypeError, ValueError):
        return 1.0
    return speed if speed > 0 else 1.0


def current_demo_timestamp(settings: Settings, now: datetime | None = None) -> datetime:
    """
    Map the real current time-of-day onto settings.demo_day, snapped to the
    nearest slot boundary. `now` is injectable for tests.

    Speed 1 (default): identical to the original implementation.
    Speed > 1 (AEGIS_DEMO_CLOCK_SPEED set): simulated time-of-day advances
    `speed`x faster than real time, anchored to this process's start.
    """
    now = now or datetime.now()
    demo_day = datetime.fromisoformat(settings.demo_day)
    speed = _demo_clock_speed()

    if speed == 1.0:
        seconds_into_day = now.hour * 3600 + now.minute * 60 + now.second
    else:
        elapsed_real_seconds = (now - _PROCESS_START).total_seconds()
        seconds_into_day = (
            _PROCESS_START_SECONDS_INTO_DAY + elapsed_real_seconds * speed
        ) % SECONDS_PER_DAY

    slot_seconds = settings.slot_minutes * 60
    snapped_seconds = (seconds_into_day // slot_seconds) * slot_seconds

    return demo_day + timedelta(seconds=snapped_seconds)


def current_slot_index(settings: Settings, now: datetime | None = None) -> int:
    ts = current_demo_timestamp(settings, now)
    demo_day = datetime.fromisoformat(settings.demo_day)
    minutes_elapsed = (ts - demo_day).total_seconds() / 60.0
    return int(minutes_elapsed // settings.slot_minutes)