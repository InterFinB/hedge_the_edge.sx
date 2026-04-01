from __future__ import annotations

from portfolio_engine.config import TICKER_TO_NAME, TICKER_TO_CATEGORY


def _round_or_none(value: float | None, digits: int = 8) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _build_top_positions(weights: dict[str, float], limit: int = 5) -> list[dict]:
    top = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [
        {
            "ticker": ticker,
            "name": TICKER_TO_NAME.get(ticker, ticker),
            "category": TICKER_TO_CATEGORY.get(ticker, "Uncategorized"),
            "weight": round(float(weight), 8),
            "weight_percent": round(float(weight) * 100, 4),
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
            "risk_contribution": round(float(value), 8),
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
            "target_return": round(float(target_return), 8),
            "target_return_percent": round(float(target_return) * 100, 4),
            "max_volatility": _round_or_none(max_volatility, 8),
            "max_volatility_percent": (
                None
                if max_volatility is None
                else round(float(max_volatility) * 100, 4)
            ),
        },
        "portfolio_outcome": {
            "expected_return": round(float(portfolio_return), 8),
            "expected_return_percent": round(float(portfolio_return) * 100, 4),
            "volatility": round(float(portfolio_volatility), 8),
            "volatility_percent": round(float(portfolio_volatility) * 100, 4),
            "active_positions": int(active_positions),
            "largest_weight": round(float(largest_weight), 8),
            "largest_weight_percent": round(float(largest_weight) * 100, 4),
            "diversification_ratio": round(float(diversification_ratio), 6),
            "concentration": round(float(concentration), 6),
            "pre_prune_assets": pre_prune_assets,
            "post_prune_assets": post_prune_assets,
            "concentration_threshold_used": _round_or_none(
                concentration_threshold_used, 6
            ),
            "concentration_capped": bool(concentration_capped),
        },
        "top_positions": _build_top_positions(weights, limit=5),
        "top_categories": category_exposure[:5],
        "top_risk_contributors": _build_top_risk_contributors(
            risk_contributions, limit=5
        ),
        "simulation": {
            "mean_return": round(float(simulation_summary["mean_return"]), 8),
            "median_return": round(float(simulation_summary["median_return"]), 8),
            "loss_probability": round(float(simulation_summary["loss_probability"]), 8),
            "percentile_5": round(float(simulation_summary["percentile_5"]), 8),
            "percentile_95": round(float(simulation_summary["percentile_95"]), 8),
        },
        "universe_status": universe_status,
        "market_data": market_data,
        "explanation": explanation,
        "selection_context": None,
    }