"""Aegis energy-data normalization service.

This module connects:

    Open-Meteo weather
            +
    configured renewable capacities
            +
    deterministic renewable engine
            +
    synthetic fallback
                    ↓
            normalized EnergySlot data

Responsibilities:
- obtain weather inputs when available
- convert weather inputs into estimated solar/wind generation
- fall back to deterministic synthetic renewable generation
- produce one normalized EnergySlot-shaped record per time slot

This module does NOT:
- run the optimizer
- calculate EV load
- make frontend decisions
- change candidate/active schedule state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.config import Settings
from app.data.external.open_meteo import WeatherRecord, get_weather_records
from app.engine.renewables import (
    calculate_solar_generation,
    calculate_total_renewable,
    calculate_wind_generation,
)


# ---------------------------------------------------------------------------
# Demo renewable-asset configuration
# ---------------------------------------------------------------------------
#
# These represent configured renewable assets, NOT live plant telemetry.
# They are deliberately kept here for the hackathon implementation instead
# of introducing another database table.
#

DEFAULT_SOLAR_CAPACITY_KW = 500.0
DEFAULT_WIND_CAPACITY_KW = 300.0
DEFAULT_SOLAR_PERFORMANCE_RATIO = 0.85


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NormalizedEnergyData:
    """Normalized energy data plus its source."""

    slots: list[dict]
    source_type: str


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


def _to_naive_timestamp(value: datetime) -> datetime:
    """Normalize a timestamp for comparison with EnergySlot timestamps.

    The existing synthetic EnergySlot dataset uses naive datetimes based on
    the configured demo timezone. Open-Meteo is requested with Asia/Kolkata,
    so we normalize incoming timestamps to the same local naive representation
    at this boundary.
    """
    if value.tzinfo is not None:
        return value.replace(tzinfo=None)

    return value


def _build_weather_lookup(
    weather_records: list[WeatherRecord],
) -> dict[datetime, WeatherRecord]:
    """Build timestamp -> weather-record lookup."""
    return {
        _to_naive_timestamp(record.timestamp): record
        for record in weather_records
    }


# ---------------------------------------------------------------------------
# Synthetic fallback
# ---------------------------------------------------------------------------


def _synthetic_solar_generation(hour: float) -> float:
    """Deterministic synthetic solar generation for fallback mode.

    Uses the same general midday-peak concept as the existing generator,
    but keeps solar and wind separate so they can be represented explicitly.
    """
    import math

    solar = 350.0 * math.exp(
        -((hour - 13.0) ** 2) / (2.0 * 3.0**2)
    )

    return max(0.0, solar)


def _synthetic_wind_generation(hour: float) -> float:
    """Deterministic synthetic wind generation for fallback mode."""
    import math

    wind = 60.0 + 20.0 * math.exp(
        -((hour - 3.0) ** 2) / (2.0 * 6.0**2)
    )

    return max(0.0, wind)


def _generate_synthetic_renewable_values(
    timestamp: datetime,
) -> tuple[float, float, float]:
    """Return deterministic synthetic solar, wind and total generation."""
    hour = timestamp.hour + timestamp.minute / 60.0

    solar = _synthetic_solar_generation(hour)
    wind = _synthetic_wind_generation(hour)
    total = calculate_total_renewable(solar, wind)

    solar = round(solar, 1)
    wind = round(wind, 1)
    total = round(
        calculate_total_renewable(
            solar_generation_kw=solar,
            wind_generation_kw=wind,
        ),
        1,
)
    return solar, wind, total


# ---------------------------------------------------------------------------
# Live weather path
# ---------------------------------------------------------------------------


def _calculate_weather_derived_generation(
    record: WeatherRecord,
    *,
    solar_capacity_kw: float,
    wind_capacity_kw: float,
    solar_performance_ratio: float,
) -> tuple[float, float, float]:
    """Convert one weather record into renewable generation."""
    solar_kw = calculate_solar_generation(
        irradiance_w_m2=record.irradiance_w_m2,
        solar_capacity_kw=solar_capacity_kw,
        performance_ratio=solar_performance_ratio,
    )

    wind_kw = calculate_wind_generation(
        wind_speed_mps=record.wind_speed_mps,
        wind_capacity_kw=wind_capacity_kw,
    )

    renewable_kw = calculate_total_renewable(
        solar_generation_kw=solar_kw,
        wind_generation_kw=wind_kw,
    )

    solar_kw = round(solar_kw, 1)
    wind_kw = round(wind_kw, 1)

    renewable_kw = round(
        calculate_total_renewable(
            solar_generation_kw=solar_kw,
            wind_generation_kw=wind_kw,
        ),
        1,
    )

    return solar_kw, wind_kw, renewable_kw


# ---------------------------------------------------------------------------
# Main normalization function
# ---------------------------------------------------------------------------


def normalize_energy_slots(
    settings: Settings,
    *,
    weather_records: list[WeatherRecord] | None = None,
    solar_capacity_kw: float = DEFAULT_SOLAR_CAPACITY_KW,
    wind_capacity_kw: float = DEFAULT_WIND_CAPACITY_KW,
    solar_performance_ratio: float = DEFAULT_SOLAR_PERFORMANCE_RATIO,
) -> NormalizedEnergyData:
    """Create normalized EnergySlot-shaped data.

    Parameters
    ----------
    settings:
        Aegis application configuration.

    weather_records:
        Optional already-fetched Open-Meteo records. Passing these explicitly
        makes the function easy to test. When omitted, the service fetches
        weather itself.

    solar_capacity_kw:
        Configured solar asset capacity.

    wind_capacity_kw:
        Configured wind asset capacity.

    solar_performance_ratio:
        Solar performance ratio.

    Returns
    -------
    NormalizedEnergyData
        48 normalized demo-horizon records by default.
    """
    demo_day = datetime.fromisoformat(settings.demo_day)

    slot_count = int(
        settings.horizon_hours * 60 / settings.slot_minutes
    )

    # If the caller does not provide weather records, attempt the live feed.
    if weather_records is None:
        weather_records = get_weather_records()

    use_live_weather = bool(weather_records)

    weather_lookup = (
        _build_weather_lookup(weather_records)
        if use_live_weather
        else {}
    )

    source_type = (
        "weather_derived"
        if use_live_weather
        else "synthetic"
    )

    normalized_slots: list[dict] = []

    for slot_index in range(slot_count):
        timestamp = demo_day + timedelta(
            minutes=slot_index * settings.slot_minutes
        )

        # ---------------------------------------------------------------
        # Renewable source selection
        # ---------------------------------------------------------------

        weather_record = weather_lookup.get(timestamp)

        if weather_record is not None:
            solar_kw, wind_kw, renewable_kw = (
                _calculate_weather_derived_generation(
                    weather_record,
                    solar_capacity_kw=solar_capacity_kw,
                    wind_capacity_kw=wind_capacity_kw,
                    solar_performance_ratio=solar_performance_ratio,
                )
            )

            slot_source_type = "weather_derived"

            observed_at = None
            forecast_for = timestamp

        else:
            # If the weather feed exists but does not have this exact slot,
            # use the deterministic synthetic value for this individual slot.
            #
            # This prevents missing timestamps from breaking the whole demo.
            solar_kw, wind_kw, renewable_kw = (
                _generate_synthetic_renewable_values(timestamp)
            )

            slot_source_type = "synthetic"

            observed_at = None
            forecast_for = timestamp

        # ---------------------------------------------------------------
        # Existing demo grid inputs
        # ---------------------------------------------------------------
        #
        # These remain synthetic/configured inputs for now.
        # We are intentionally not changing the architecture of base load,
        # price, carbon intensity, or grid capacity in this task.
        #

        hour = timestamp.hour + timestamp.minute / 60.0

        import math

        morning = 250.0 * math.exp(
            -((hour - 8.5) ** 2) / (2.0 * 2.0**2)
        )
        evening = 400.0 * math.exp(
            -((hour - 19.0) ** 2) / (2.0 * 2.5**2)
        )

        base_load_kw = round(300.0 + morning + evening, 1)

        grid_capacity_kw = 2200.0

        renewable_share = min(
            1.0,
            renewable_kw / max(base_load_kw, 1.0),
        )

        electricity_price = round(
            8.0 * (1.15 - 0.35 * renewable_share),
            2,
        )

        carbon_intensity = round(
            0.75 * (1.0 - 0.7 * renewable_share),
            3,
        )

        normalized_slots.append(
            {
                "timestamp": timestamp,
                "base_load_kw": base_load_kw,
                "grid_capacity_kw": grid_capacity_kw,
                "solar_generation_kw": solar_kw,
                "wind_generation_kw": wind_kw,
                "renewable_kw": renewable_kw,
                "electricity_price": max(
                    electricity_price,
                    1.0,
                ),
                "carbon_intensity": max(
                    carbon_intensity,
                    0.05,
                ),
                "source_type": slot_source_type,
                "observed_at": observed_at,
                "forecast_for": forecast_for,
            }
        )

    return NormalizedEnergyData(
        slots=normalized_slots,
        source_type=source_type,
    )


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------


def get_normalized_energy_data(
    settings: Settings,
    *,
    latitude: float = 23.03,
    longitude: float = 72.58,
) -> NormalizedEnergyData:
    """Fetch weather and return normalized EnergySlot data.

    Open-Meteo failure automatically falls back to deterministic synthetic
    renewable data.

    The coordinates default to the Ahmedabad/Gandhinagar region for the
    hackathon demo and can be changed later through configuration.
    """
    weather_records = get_weather_records(
        latitude=latitude,
        longitude=longitude,
    )

    return normalize_energy_slots(
        settings,
        weather_records=weather_records,
    )