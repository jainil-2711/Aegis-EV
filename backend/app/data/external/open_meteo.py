"""
Aegis — Optional Open-Meteo adapter (P1, Phase 6)

External renewable/weather enrichment is OPTIONAL (PRD.md SS12,
architecture.md SS11). This module must:
  - never be called directly by the optimizer (architecture.md SS7),
  - always have a synthetic fallback,
  - never block startup or the demo if the network call fails.

Wire this in behind app/data/synthetic/generator.py's renewable_kw values
by calling `enrich_with_weather()` on a slot list; on any failure it
returns the input unchanged.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("aegis.external.open_meteo")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_solar_wind_forecast(latitude: float, longitude: float) -> dict | None:
    """
    Best-effort fetch of solar/wind-relevant fields from Open-Meteo.
    Returns None on any failure so callers can fall back to synthetic data.
    This function intentionally has no retry/backoff logic — for a
    hackathon demo, one failed attempt should fall back immediately
    (architecture.md SS16 "reliability").
    """
    try:
        import httpx

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "shortwave_radiation,wind_speed_10m",
            "forecast_days": 1,
        }
        response = httpx.get(OPEN_METEO_URL, params=params, timeout=3.0)
        response.raise_for_status()
        return response.json()
    except Exception as exc:  # noqa: BLE001 - deliberate broad catch, see docstring
        logger.warning("Open-Meteo fetch failed, falling back to synthetic: %s", exc)
        return None


def enrich_with_weather(
    slots: list[dict], latitude: float = 23.03, longitude: float = 72.58
) -> list[dict]:
    """
    Attempt to nudge synthetic renewable_kw values using real solar/wind
    data. On any failure, or if the response shape is unexpected, returns
    `slots` completely unchanged — synthetic data is the guaranteed
    fallback (PRD.md SS12).
    """
    forecast = fetch_solar_wind_forecast(latitude, longitude)
    if not forecast:
        return slots

    try:
        hourly = forecast["hourly"]
        radiation = hourly["shortwave_radiation"]
        wind = hourly["wind_speed_10m"]
    except (KeyError, TypeError):
        return slots

    enriched = []
    for i, slot in enumerate(slots):
        hour_index = min(i // 2, len(radiation) - 1, len(wind) - 1)
        if hour_index < 0:
            enriched.append(slot)
            continue
        # Blend: keep the synthetic baseline shape, nudge magnitude toward
        # real conditions rather than replacing it outright.
        solar_factor = 1.0 + (radiation[hour_index] / 1000.0 - 0.3)
        wind_factor = 1.0 + (wind[hour_index] / 20.0 - 0.3)
        blended = dict(slot)
        blended["renewable_kw"] = round(
            max(0.0, slot["renewable_kw"] * (0.7 + 0.3 * ((solar_factor + wind_factor) / 2))),
            1,
        )
        enriched.append(blended)

    return enriched
