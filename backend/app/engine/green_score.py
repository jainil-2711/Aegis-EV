"""Deterministic, transparent, non-punitive Green Score for Aegis."""

from __future__ import annotations


def calculate_green_score(
    *,
    renewable_share_pct: float,
    average_carbon_intensity: float,
    grid_energy_kwh: float,
    total_energy_kwh: float,
) -> float:
    """Return a 0–100 informational score.

    65% renewable alignment, 25% carbon cleanliness and 10% grid reliance.
    The score evaluates the delivered energy rather than rewarding a driver
    for simply receiving less energy.
    """
    renewable = max(0.0, min(100.0, renewable_share_pct))
    carbon_score = max(0.0, min(100.0, (1.0 - max(0.0, average_carbon_intensity)) * 100.0))
    grid_ratio = (max(0.0, grid_energy_kwh) / total_energy_kwh) if total_energy_kwh > 0 else 0.0
    grid_cleanliness = max(0.0, min(100.0, (1.0 - grid_ratio) * 100.0))
    score = 0.65 * renewable + 0.25 * carbon_score + 0.10 * grid_cleanliness
    return round(max(0.0, min(100.0, score)), 0)
