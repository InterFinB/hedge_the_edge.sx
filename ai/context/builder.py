from __future__ import annotations

from portfolio_engine.config import TICKER_TO_NAME, TICKER_TO_CATEGORY


def _round(value, digits=8):
    try:
        return round(float(value), digits)
    except Exception:
        return 0.0


def _round_or_none(value, digits=8):
    if value is None:
        return None
    return _round(value, digits)


def _build_top_positions(weights: dict[str, float], limit: int = 5) -> list[dict]:
    top = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:limit]

    return [
        {
            "ticker": ticker,
            "name": TICKER_TO_NAME.get(ticker, ticker),
            "category": TICKER_TO_CATEGORY.get(ticker, "Uncategorized"),
            "weight": _round(weight, 8),
            "weight_percent": _round(weight * 100, 4),
        }
        for ticker, weight in top
    ]


def _build_top_risk_contributors(
    risk_contributions: dict[str, float],
    limit: int = 5,
) -> list[dict]:
    top = sorted(risk_contributions.items(), key=lambda x: x[1], reverse=True)[:limit]

    return [
        {
            "ticker": ticker,
            "name": TICKER_TO_NAME.get(ticker, ticker),
            "category": TICKER_TO_CATEGORY.get(ticker, "Uncategorized"),
            "risk_contribution": _round(value, 8),
        }
        for ticker, value in top
    ]


def build_ai_context(
    *,
    target_return: float,
    max_volatility: float | None,
    portfolio_return: float,
    portfolio_volatility: float,
    weights: dict[str, float],
    category_exposure: list[dict],
    risk_contributions: dict[str, float],
    diversification_ratio: float,
    concentration: float,
    active_positions: int,
    largest_weight: float,
    pre_prune_assets: int | None,
    post_prune_assets: int | None,
    concentration_threshold_used: float | None,
    concentration_capped: bool,
    simulation_summary: dict,
    universe_status: dict,
    market_data: dict,
    explanation: dict | str | None = None,
) -> dict:
    return {
        "portfolio_objective": {
            "target_return": _round(target_return),
            "target_return_percent": _round(target_return * 100, 4),
            "max_volatility": _round_or_none(max_volatility),
            "max_volatility_percent": (
                None if max_volatility is None else _round(max_volatility * 100, 4)
            ),
        },
        "portfolio_outcome": {
            "expected_return": _round(portfolio_return),
            "expected_return_percent": _round(portfolio_return * 100, 4),
            "volatility": _round(portfolio_volatility),
            "volatility_percent": _round(portfolio_volatility * 100, 4),
            "active_positions": int(active_positions),
            "largest_weight": _round(largest_weight),
            "largest_weight_percent": _round(largest_weight * 100, 4),
            "diversification_ratio": _round(diversification_ratio, 6),
            "concentration": _round(concentration, 6),
            "pre_prune_assets": pre_prune_assets,
            "post_prune_assets": post_prune_assets,
            "concentration_threshold_used": _round_or_none(
                concentration_threshold_used, 6
            ),
            "concentration_capped": bool(concentration_capped),
        },
        "top_positions": _build_top_positions(weights),
        "top_categories": category_exposure[:5],
        "top_risk_contributors": _build_top_risk_contributors(risk_contributions),
        "simulation": {
            "mean_return": _round(simulation_summary.get("mean_return")),
            "median_return": _round(simulation_summary.get("median_return")),
            "loss_probability": _round(simulation_summary.get("loss_probability")),
            "percentile_5": _round(simulation_summary.get("percentile_5")),
            "percentile_95": _round(simulation_summary.get("percentile_95")),
        },
        "universe_status": universe_status or {},
        "market_data": market_data or {},
        "explanation": explanation,
        "selection_context": None,
    }