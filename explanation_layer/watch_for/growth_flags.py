from portfolio_engine.config import (
    TICKER_TO_CATEGORY,
    CATEGORY_BASELINE_RETURNS,
)

from ..utils import get_active_assets


def _get_category_baseline(ticker):

    category = TICKER_TO_CATEGORY.get(ticker)

    if category is None:
        return 0.08

    return CATEGORY_BASELINE_RETURNS.get(category, 0.08)


def generate_growth_flags(
    weights,
    risk_contributions,
    expected_portfolio_return,
):

    items = []

    active_assets = get_active_assets(weights)

    if not active_assets:
        return items

    sorted_weights = sorted(
        active_assets.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    high_return_environment = expected_portfolio_return >= 0.11

    for ticker, weight in sorted_weights:

        rc = risk_contributions.get(ticker, 0.0)

        if (
            high_return_environment
            and weight >= 0.12
            and rc > 0
        ):

            category = TICKER_TO_CATEGORY.get(ticker, "asset")

            items.append(
                {
                    "kind": "return_assumption",
                    "asset": ticker,
                    "priority": 85,
                    "message": (
                        f"Watch {ticker}: part of its allocation reflects strong expected return assumptions "
                        f"relative to the {category} baseline. "
                        f"If expected return estimates decline, recompute the portfolio."
                    ),
                }
            )

    return items[:2]