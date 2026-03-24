from dataclasses import dataclass


@dataclass
class RecomputeSchedule:
    portfolio_volatility: float
    interval_label: str
    interval_days: int
    rationale: str


def normalize_volatility(volatility: float) -> float:
    if volatility is None:
        raise ValueError("portfolio volatility cannot be None")

    if volatility > 1:
        return volatility / 100.0

    return volatility


def get_recompute_schedule(portfolio_volatility: float) -> RecomputeSchedule:
    vol = normalize_volatility(portfolio_volatility)

    if vol > 0.25:
        return RecomputeSchedule(
            portfolio_volatility=vol,
            interval_label="7 days",
            interval_days=7,
            rationale="The portfolio is in a high-volatility regime, so the optimal allocation can become outdated quickly.",
        )
    if vol > 0.15:
        return RecomputeSchedule(
            portfolio_volatility=vol,
            interval_label="2 weeks",
            interval_days=14,
            rationale="The portfolio has elevated volatility, so it should be monitored and recomputed relatively frequently.",
        )
    if vol > 0.08:
        return RecomputeSchedule(
            portfolio_volatility=vol,
            interval_label="1 month",
            interval_days=30,
            rationale="The portfolio is in a moderate volatility regime, so monthly recomputation is sufficient.",
        )
    if vol > 0.04:
        return RecomputeSchedule(
            portfolio_volatility=vol,
            interval_label="2 months",
            interval_days=60,
            rationale="The portfolio is relatively stable, so recomputation can be less frequent.",
        )

    return RecomputeSchedule(
        portfolio_volatility=vol,
        interval_label="3 months",
        interval_days=90,
        rationale="The portfolio is in a low-volatility regime, so the allocation is likely to remain stable for longer.",
    )