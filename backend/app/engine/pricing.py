"""Deterministic, bounded, non-punitive pricing rule (P2-owned)."""

from sqlalchemy.orm import Session

from app.schemas.enums import GridCondition
from app.schemas.shared import PricingRule, PricingTier


_BASE_RATE = 7.0
_TIERS = (
    PricingTier(condition=GridCondition.high_renewable, price_per_kwh=5.0),
    PricingTier(condition=GridCondition.normal, price_per_kwh=7.0),
    PricingTier(condition=GridCondition.low_renewable, price_per_kwh=9.0),
    PricingTier(condition=GridCondition.high_demand, price_per_kwh=10.0),
)


def get_current_pricing_rule(db: Session) -> PricingRule:
    """Return the canonical demo pricing rule.

    The current MVP pricing rule is deterministic and bounded. It is surfaced
    inside operator/driver responses rather than through a dedicated endpoint.
    ``db`` is accepted so the service can evolve to a scenario-aware rule
    without changing callers or introducing another data source boundary.
    """
    _ = db
    return PricingRule(base_rate=_BASE_RATE, currency="INR", tiers=list(_TIERS))
