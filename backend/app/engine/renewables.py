"""Deterministic renewable generation calculations for Aegis.

This module converts weather inputs into estimated renewable generation.

Important:
- This module does NOT make HTTP requests.
- This module does NOT access the database.
- This module does NOT know about FastAPI.
- Weather measurements are converted into estimated generation using
  configured renewable asset capacities.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Solar configuration
# ---------------------------------------------------------------------------

DEFAULT_SOLAR_PERFORMANCE_RATIO = 0.85


# ---------------------------------------------------------------------------
# Demo wind turbine configuration
# ---------------------------------------------------------------------------
#
# These values define a normalized demo turbine power curve.
# They are NOT intended to represent a specific commercial turbine.
#
# Below cut-in:
#     no useful generation
#
# Cut-in -> rated:
#     output rises linearly from 0% to 100%
#
# Rated -> cut-out:
#     output remains at 100%
#
# Above cut-out:
#     turbine is assumed shut down for protection
#

DEFAULT_WIND_CUT_IN_MPS = 3.0
DEFAULT_WIND_RATED_MPS = 12.0
DEFAULT_WIND_CUT_OUT_MPS = 25.0


def calculate_solar_generation(
    irradiance_w_m2: float,
    solar_capacity_kw: float,
    performance_ratio: float = DEFAULT_SOLAR_PERFORMANCE_RATIO,
) -> float:
    """Calculate estimated solar generation in kW.

    Parameters
    ----------
    irradiance_w_m2:
        Solar irradiance in watts per square metre.

    solar_capacity_kw:
        Installed solar capacity in kW.

    performance_ratio:
        Dimensionless conversion/performance factor, normally between 0 and 1.

    Returns
    -------
    float
        Estimated solar generation in kW.
    """
    if irradiance_w_m2 < 0:
        raise ValueError("irradiance_w_m2 cannot be negative")

    if solar_capacity_kw < 0:
        raise ValueError("solar_capacity_kw cannot be negative")

    if not 0 <= performance_ratio <= 1:
        raise ValueError("performance_ratio must be between 0 and 1")

    generation_kw = (
        (irradiance_w_m2 / 1000.0)
        * solar_capacity_kw
        * performance_ratio
    )

    # Never return negative generation.
    return max(0.0, generation_kw)


def _normalized_wind_power_fraction(
    wind_speed_mps: float,
    *,
    cut_in_mps: float = DEFAULT_WIND_CUT_IN_MPS,
    rated_mps: float = DEFAULT_WIND_RATED_MPS,
    cut_out_mps: float = DEFAULT_WIND_CUT_OUT_MPS,
) -> float:
    """Return normalized wind output between 0 and 1.

    Demo piecewise power curve:

    v < cut-in
        -> 0

    cut-in <= v < rated
        -> linear ramp from 0 to 1

    rated <= v <= cut-out
        -> 1

    v > cut-out
        -> 0
    """
    if wind_speed_mps < 0:
        raise ValueError("wind_speed_mps cannot be negative")

    if not (
        0 < cut_in_mps < rated_mps < cut_out_mps
    ):
        raise ValueError(
            "wind curve requires 0 < cut_in < rated < cut_out"
        )

    if wind_speed_mps < cut_in_mps:
        return 0.0

    if wind_speed_mps < rated_mps:
        return (wind_speed_mps - cut_in_mps) / (
            rated_mps - cut_in_mps
        )

    if wind_speed_mps <= cut_out_mps:
        return 1.0

    return 0.0


def calculate_wind_generation(
    wind_speed_mps: float,
    wind_capacity_kw: float,
    *,
    cut_in_mps: float = DEFAULT_WIND_CUT_IN_MPS,
    rated_mps: float = DEFAULT_WIND_RATED_MPS,
    cut_out_mps: float = DEFAULT_WIND_CUT_OUT_MPS,
) -> float:
    """Calculate estimated wind generation in kW.

    Parameters
    ----------
    wind_speed_mps:
        Wind speed in metres per second.

    wind_capacity_kw:
        Installed wind capacity in kW.

    cut_in_mps:
        Wind speed at which useful generation starts.

    rated_mps:
        Wind speed at which rated output is reached.

    cut_out_mps:
        Wind speed above which the turbine is assumed to shut down.

    Returns
    -------
    float
        Estimated wind generation in kW.
    """
    if wind_capacity_kw < 0:
        raise ValueError("wind_capacity_kw cannot be negative")

    fraction = _normalized_wind_power_fraction(
        wind_speed_mps,
        cut_in_mps=cut_in_mps,
        rated_mps=rated_mps,
        cut_out_mps=cut_out_mps,
    )

    generation_kw = wind_capacity_kw * fraction

    return max(0.0, generation_kw)


def calculate_total_renewable(
    solar_generation_kw: float,
    wind_generation_kw: float,
) -> float:
    """Calculate canonical total renewable generation.

    Aegis invariant:

        renewable_kw
            = solar_generation_kw + wind_generation_kw
    """
    if solar_generation_kw < 0:
        raise ValueError("solar_generation_kw cannot be negative")

    if wind_generation_kw < 0:
        raise ValueError("wind_generation_kw cannot be negative")

    return solar_generation_kw + wind_generation_kw