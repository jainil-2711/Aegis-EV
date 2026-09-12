"""
Aegis — Open-Meteo weather adapter.

Responsibilities
----------------
This module is responsible only for retrieving and normalizing weather data.

It does NOT:
- calculate solar generation
- calculate wind generation
- create/update EnergySlot database rows
- access the database
- call the optimizer

The renewable generation calculation belongs to:
    backend/app/engine/renewables.py

The normalized output from this module is intended to be consumed by:
    backend/app/services/grid/energy_data.py

Failure behavior
----------------
Open-Meteo is an optional external dependency. Any network/API/parsing
failure returns None so the caller can fall back to deterministic synthetic
data.

Timezone
--------
The returned timestamps preserve the timezone information supplied by
Open-Meteo. The normalizer is responsible for aligning those timestamps with
the Aegis configured timezone and EnergySlot timestamps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger("aegis.external.open_meteo")

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class WeatherRecord:
    """Normalized weather input for one forecast timestamp.

    These are weather measurements/forecast inputs, NOT power generation.
    """

    timestamp: datetime
    irradiance_w_m2: float
    wind_speed_mps: float


def fetch_solar_wind_forecast(
    latitude: float,
    longitude: float,
) -> dict[str, Any] | None:
    """Fetch solar/wind-relevant forecast data from Open-Meteo.

    Returns the raw JSON dictionary on success.

    Returns None on any network, HTTP, or parsing failure so that the
    application can use synthetic renewable data instead.
    """
    try:
        import httpx

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "shortwave_radiation,wind_speed_10m",
            "forecast_days": 1,
            "timezone": "Asia/Kolkata",
        }

        response = httpx.get(
            OPEN_METEO_URL,
            params=params,
            timeout=3.0,
        )
        response.raise_for_status()

        payload = response.json()

        if not isinstance(payload, dict):
            logger.warning(
                "Open-Meteo returned an unexpected payload type: %s",
                type(payload).__name__,
            )
            return None

        return payload

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Open-Meteo fetch failed, synthetic fallback will be used: %s",
            exc,
        )
        return None


def _parse_weather_records(
    forecast: dict[str, Any],
) -> list[WeatherRecord]:
    """Convert Open-Meteo's hourly response into normalized records."""

    hourly = forecast.get("hourly")
    if not isinstance(hourly, dict):
        raise ValueError("Open-Meteo response does not contain valid hourly data")

    timestamps = hourly.get("time")
    radiation = hourly.get("shortwave_radiation")
    wind = hourly.get("wind_speed_10m")

    if not isinstance(timestamps, list):
        raise ValueError("Open-Meteo hourly.time is missing or invalid")

    if not isinstance(radiation, list):
        raise ValueError(
            "Open-Meteo hourly.shortwave_radiation is missing or invalid"
        )

    if not isinstance(wind, list):
        raise ValueError(
            "Open-Meteo hourly.wind_speed_10m is missing or invalid"
        )

    record_count = min(
        len(timestamps),
        len(radiation),
        len(wind),
    )

    records: list[WeatherRecord] = []

    for index in range(record_count):
        timestamp_value = timestamps[index]
        radiation_value = radiation[index]
        wind_value = wind[index]

        try:
            timestamp = datetime.fromisoformat(timestamp_value)
            irradiance_w_m2 = float(radiation_value or 0.0)
            wind_speed_mps = float(wind_value or 0.0)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "Skipping malformed Open-Meteo record at index %s: %s",
                index,
                exc,
            )
            continue

        if irradiance_w_m2 < 0:
            irradiance_w_m2 = 0.0

        if wind_speed_mps < 0:
            wind_speed_mps = 0.0

        records.append(
            WeatherRecord(
                timestamp=timestamp,
                irradiance_w_m2=irradiance_w_m2,
                wind_speed_mps=wind_speed_mps,
            )
        )

    if not records:
        raise ValueError("Open-Meteo response contained no valid weather records")

    return records


def get_weather_records(
    latitude: float = 23.03,
    longitude: float = 72.58,
) -> list[WeatherRecord] | None:
    """Fetch and normalize Open-Meteo weather data.

    Returns:
        A list of normalized WeatherRecord objects on success.
        None when the external feed is unavailable or malformed.
    """
    forecast = fetch_solar_wind_forecast(
        latitude=latitude,
        longitude=longitude,
    )

    if forecast is None:
        return None

    try:
        return _parse_weather_records(forecast)
    except (TypeError, ValueError, KeyError) as exc:
        logger.warning(
            "Open-Meteo response normalization failed; "
            "synthetic fallback will be used: %s",
            exc,
        )
        return None