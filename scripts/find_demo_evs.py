"""
Aegis — demo-EV finder.

Classifies every seeded EV by whether its own arrival/departure window
creates a *genuine* cheapest/greenest/balanced/immediate trade-off, or
whether it's structurally guaranteed to converge to the same slot under
every objective (because its window fully contains the midday
renewable-surplus peak).

This is read-only and touches no database — it regenerates the exact same
deterministic dataset your seed_demo.py produces (same seed, same
demo_day) and just inspects it, so the EV ids it prints are guaranteed to
match what's actually sitting in your DB right now.

Usage (from repo root, same way you'd run seed_demo.py):
    python scripts/find_demo_evs.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings  # noqa: E402
from app.data.synthetic.generator import (  # noqa: E402
    _gaussian_bump,
    generate_full_dataset,
)


def _renewable_share_at_hour(hour: float) -> float:
    """Mirrors generate_energy_slots' price/carbon renewable_share calc,
    without the per-slot random noise, so this is the *expected* curve
    shape rather than one exact seeded slot's noisy value. Good enough to
    classify "is this hour structurally in the cheap/green peak or not" —
    exact per-slot values are re-checked below from the real generated
    energy_slots, not from this approximation alone.
    """
    morning = 250.0 * _gaussian_bump(hour, peak=8.5, width=2.0)
    evening = 400.0 * _gaussian_bump(hour, peak=19.0, width=2.5)
    base_load_kw = 300.0 + morning + evening

    solar = 350.0 * _gaussian_bump(hour, peak=13.0, width=3.0)
    wind = 60.0 + 20.0 * _gaussian_bump(hour, peak=3.0, width=6.0)
    renewable_kw = solar + wind

    return min(1.0, renewable_kw / max(base_load_kw, 1.0))


def main() -> None:
    settings = get_settings()
    dataset = generate_full_dataset(settings)

    # Use the *actual* generated energy_slots (with their real noise
    # applied) to find the real high-renewable window for this exact seed,
    # rather than trusting the noise-free approximation above.
    slot_shares = []
    for slot in dataset.energy_slots:
        ts = slot["timestamp"]
        hour = ts.hour + ts.minute / 60.0
        share = min(1.0, max(0.0, slot["renewable_kw"]) / max(slot["base_load_kw"], 1.0))
        slot_shares.append((ts, hour, share))

    HIGH_RENEWABLE_THRESHOLD = 0.80
    high_renewable_hours = {hour for _, hour, share in slot_shares if share >= HIGH_RENEWABLE_THRESHOLD}
    if high_renewable_hours:
        peak_start, peak_end = min(high_renewable_hours), max(high_renewable_hours)
    else:
        peak_start = peak_end = None

    print(f"Seed={settings.seed}  demo_day={settings.demo_day}")
    if peak_start is not None:
        print(
            f"High-renewable window this seed produces (share >= {HIGH_RENEWABLE_THRESHOLD:.0%}): "
            f"~{peak_start:.1f}h - {peak_end:.1f}h\n"
        )
    else:
        print("No slot reached the high-renewable threshold this seed — check the generator settings.\n")

    dominant: list[dict] = []
    tradeoff: list[dict] = []
    non_flexible: list[dict] = []

    for ev in dataset.evs:
        arrival_h = ev["arrival_time"].hour + ev["arrival_time"].minute / 60.0
        departure_h = ev["departure_time"].hour + ev["departure_time"].minute / 60.0
        # departure can roll past midnight relative to arrival in the raw
        # generator output; normalize for a simple same-day overlap check.
        if departure_h < arrival_h:
            departure_h += 24.0

        window_hours = departure_h - arrival_h
        contains_peak = (
            peak_start is not None and arrival_h <= peak_start and departure_h >= peak_end
        )
        excludes_peak = (
            peak_start is not None and (departure_h <= peak_start or arrival_h >= peak_end)
        )

        record = {
            "id": ev["id"],
            "profile": ev["profile"],
            "flexibility": ev["flexibility"],
            "arrival": f"{arrival_h:.1f}h",
            "departure": f"{departure_h:.1f}h",
            "window_hours": round(window_hours, 1),
            "preference": ev["preference"],
            "soc": f"{ev['current_soc']:.0f}%->{ev['target_soc']:.0f}%",
        }

        if ev["flexibility"] == "non_flexible":
            non_flexible.append(record)
        elif excludes_peak:
            tradeoff.append(record)
        elif contains_peak:
            dominant.append(record)
        # partial-overlap EVs are left unclassified on purpose — they're
        # the ambiguous middle ground, not a clean demo case either way.

    def _print_group(title: str, group: list[dict], note: str) -> None:
        print(f"=== {title} ({len(group)} EVs) ===")
        print(f"{note}\n")
        for rec in group[:8]:
            print(
                f"  {rec['id']:8s}  profile={rec['profile']:10s} flex={rec['flexibility']:13s} "
                f"window={rec['arrival']}->{rec['departure']} ({rec['window_hours']}h)  "
                f"soc={rec['soc']:12s} default_pref={rec['preference']}"
            )
        if len(group) > 8:
            print(f"  ... and {len(group) - 8} more")
        print()

    _print_group(
        "GENUINE TRADE-OFF candidates — window excludes the renewable peak",
        tradeoff,
        "Expect cheapest/greenest/balanced/immediate to actually pick different windows here.",
    )
    _print_group(
        "NON-FLEXIBLE — required charging time >= their window",
        non_flexible,
        "Expect near-identical output regardless of preference: correctly demonstrates "
        "'physical constraints always win over preference.'",
    )
    _print_group(
        "DOMINANT-SLOT — window fully contains the renewable peak",
        dominant,
        "Expect near-identical output regardless of preference: correctly demonstrates "
        "'the system doesn't invent a fake trade-off when there isn't one.'",
    )

    print(
        "Suggested 4-EV demo set: pick 1-2 from GENUINE TRADE-OFF (to show divergence), "
        "1 from NON-FLEXIBLE (to show constraints beat preference), and 1 from DOMINANT-SLOT "
        "(to show correct convergence). That's the full story in 4 logins."
    )


if __name__ == "__main__":
    main()