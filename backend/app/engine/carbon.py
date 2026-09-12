"""Authoritative environmental accounting for Aegis."""

from __future__ import annotations


def renewable_share_pct(total_energy_kwh: float, renewable_energy_kwh: float) -> float:
    if total_energy_kwh <= 0:
        return 0.0
    return max(0.0, min(100.0, renewable_energy_kwh / total_energy_kwh * 100.0))


def co2_kg_from_grid(grid_energy_kwh: float, carbon_intensity_kg_per_kwh: float) -> float:
    return max(0.0, grid_energy_kwh) * max(0.0, carbon_intensity_kg_per_kwh)


def reduction_pct(baseline: float, optimized: float) -> float:
    if baseline <= 0:
        return 0.0
    return (baseline - optimized) / baseline * 100.0
