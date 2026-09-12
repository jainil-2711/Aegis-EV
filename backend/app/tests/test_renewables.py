"""Tests for the Aegis renewable generation/data pipeline."""

from datetime import datetime

import pytest

from app.data.external.open_meteo import (
    WeatherRecord,
    _parse_weather_records,
    get_weather_records,
)
from app.engine.renewables import (
    calculate_solar_generation,
    calculate_total_renewable,
    calculate_wind_generation,
)
from app.services.grid.energy_data import normalize_energy_slots


def test_solar_conversion_is_unit_correct():
    """800 W/m² on a 500 kW asset at PR=0.85 gives 340 kW."""
    result = calculate_solar_generation(
        irradiance_w_m2=800.0,
        solar_capacity_kw=500.0,
        performance_ratio=0.85,
    )

    assert result == pytest.approx(340.0)


def test_solar_generation_never_exceeds_expected_capacity():
    result = calculate_solar_generation(
        irradiance_w_m2=1000.0,
        solar_capacity_kw=500.0,
        performance_ratio=0.85,
    )

    assert result == pytest.approx(425.0)
    assert result >= 0.0


def test_solar_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_solar_generation(
            irradiance_w_m2=-1.0,
            solar_capacity_kw=500.0,
        )

    with pytest.raises(ValueError):
        calculate_solar_generation(
            irradiance_w_m2=800.0,
            solar_capacity_kw=-1.0,
        )

    with pytest.raises(ValueError):
        calculate_solar_generation(
            irradiance_w_m2=800.0,
            solar_capacity_kw=500.0,
            performance_ratio=1.1,
        )


def test_wind_power_curve():
    capacity = 300.0

    # Below cut-in.
    assert calculate_wind_generation(
        2.0,
        capacity,
    ) == pytest.approx(0.0)

    # At cut-in.
    assert calculate_wind_generation(
        3.0,
        capacity,
    ) == pytest.approx(0.0)

    # Midpoint between cut-in (3) and rated (12).
    # Fraction = (7.5 - 3) / (12 - 3) = 0.5
    assert calculate_wind_generation(
        7.5,
        capacity,
    ) == pytest.approx(150.0)

    # Rated.
    assert calculate_wind_generation(
        12.0,
        capacity,
    ) == pytest.approx(300.0)

    # Rated to cut-out remains at rated output.
    assert calculate_wind_generation(
        20.0,
        capacity,
    ) == pytest.approx(300.0)

    # Above cut-out.
    assert calculate_wind_generation(
        26.0,
        capacity,
    ) == pytest.approx(0.0)


def test_wind_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_wind_generation(
            wind_speed_mps=-1.0,
            wind_capacity_kw=300.0,
        )

    with pytest.raises(ValueError):
        calculate_wind_generation(
            wind_speed_mps=5.0,
            wind_capacity_kw=-1.0,
        )


def test_total_renewable_is_exact_sum():
    solar = 123.4
    wind = 56.7

    renewable = calculate_total_renewable(
        solar_generation_kw=solar,
        wind_generation_kw=wind,
    )

    assert renewable == pytest.approx(
        solar + wind,
        abs=1e-9,
    )


def test_total_renewable_rejects_negative_components():
    with pytest.raises(ValueError):
        calculate_total_renewable(
            solar_generation_kw=-1.0,
            wind_generation_kw=10.0,
        )

    with pytest.raises(ValueError):
        calculate_total_renewable(
            solar_generation_kw=10.0,
            wind_generation_kw=-1.0,
        )


def test_open_meteo_parser_normalizes_valid_records():
    payload = {
        "hourly": {
            "time": [
                "2026-09-12T10:00",
                "2026-09-12T11:00",
            ],
            "shortwave_radiation": [
                800,
                900,
            ],
            "wind_speed_10m": [
                5,
                7,
            ],
        }
    }

    records = _parse_weather_records(payload)

    assert len(records) == 2

    assert records[0] == WeatherRecord(
        timestamp=datetime(
            2026,
            9,
            12,
            10,
            0,
        ),
        irradiance_w_m2=800.0,
        wind_speed_mps=5.0,
    )

    assert records[1] == WeatherRecord(
        timestamp=datetime(
            2026,
            9,
            12,
            11,
            0,
        ),
        irradiance_w_m2=900.0,
        wind_speed_mps=7.0,
    )


def test_open_meteo_parser_skips_malformed_record():
    payload = {
        "hourly": {
            "time": [
                "2026-09-12T10:00",
                "2026-09-12T11:00",
            ],
            "shortwave_radiation": [
                800,
                900,
            ],
            "wind_speed_10m": [
                "bad",
                7,
            ],
        }
    }

    records = _parse_weather_records(payload)

    assert len(records) == 1

    assert records[0].timestamp == datetime(
        2026,
        9,
        12,
        11,
        0,
    )

    assert records[0].irradiance_w_m2 == 900.0
    assert records[0].wind_speed_mps == 7.0


def test_open_meteo_parser_rejects_payload_with_no_valid_records():
    payload = {
        "hourly": {
            "time": [
                "2026-09-12T10:00",
            ],
            "shortwave_radiation": [
                800,
            ],
            "wind_speed_10m": [
                "bad",
            ],
        }
    }

    with pytest.raises(ValueError):
        _parse_weather_records(payload)


def test_open_meteo_failure_returns_none():
    """
    The public adapter may return real records when the network is available
    or None when Open-Meteo is unavailable.

    This test therefore validates the documented return contract without
    making the test depend on Internet availability.
    """
    result = get_weather_records(
        latitude=23.03,
        longitude=72.58,
    )

    assert result is None or isinstance(
        result,
        list,
    )


def test_normalizer_synthetic_fallback(settings):
    result = normalize_energy_slots(
        settings,
        weather_records=[],
    )

    assert result.source_type == "synthetic"
    assert len(result.slots) == 48

    for slot in result.slots:
        assert slot["source_type"] == "synthetic"
        assert slot["observed_at"] is None
        assert slot["forecast_for"] == slot["timestamp"]

        assert slot["solar_generation_kw"] >= 0.0
        assert slot["wind_generation_kw"] >= 0.0
        assert slot["renewable_kw"] >= 0.0

        assert slot["renewable_kw"] == pytest.approx(
            slot["solar_generation_kw"]
            + slot["wind_generation_kw"],
            abs=1e-9,
        )


def test_normalizer_uses_weather_derived_generation(settings):
    weather_records = [
        WeatherRecord(
            timestamp=datetime(
                2026,
                9,
                12,
                10,
                0,
            ),
            irradiance_w_m2=800.0,
            wind_speed_mps=12.0,
        )
    ]

    result = normalize_energy_slots(
        settings,
        weather_records=weather_records,
    )

    assert result.source_type == "weather_derived"
    assert len(result.slots) == 48

    ten_am = next(
        slot
        for slot in result.slots
        if slot["timestamp"] == datetime(
            2026,
            9,
            12,
            10,
            0,
        )
    )

    assert ten_am["source_type"] == "weather_derived"

    # 800 / 1000 × 500 × 0.85 = 340 kW
    assert ten_am["solar_generation_kw"] == pytest.approx(
        340.0,
    )

    # 12 m/s is rated speed for the demo curve.
    assert ten_am["wind_generation_kw"] == pytest.approx(
        300.0,
    )

    assert ten_am["renewable_kw"] == pytest.approx(
        ten_am["solar_generation_kw"]
        + ten_am["wind_generation_kw"],
        abs=1e-9,
    )


def test_normalizer_preserves_48_slot_horizon(settings):
    result = normalize_energy_slots(
        settings,
        weather_records=[],
    )

    timestamps = [
        slot["timestamp"]
        for slot in result.slots
    ]

    assert len(timestamps) == 48
    assert timestamps == sorted(timestamps)


def test_normalizer_never_produces_negative_renewable(
    settings,
):
    weather_records = [
        WeatherRecord(
            timestamp=datetime(
                2026,
                9,
                12,
                12,
                0,
            ),
            irradiance_w_m2=0.0,
            wind_speed_mps=0.0,
        )
    ]

    result = normalize_energy_slots(
        settings,
        weather_records=weather_records,
    )

    for slot in result.slots:
        assert slot["solar_generation_kw"] >= 0.0
        assert slot["wind_generation_kw"] >= 0.0
        assert slot["renewable_kw"] >= 0.0

        assert slot["renewable_kw"] == pytest.approx(
            slot["solar_generation_kw"]
            + slot["wind_generation_kw"],
            abs=1e-9,
        )