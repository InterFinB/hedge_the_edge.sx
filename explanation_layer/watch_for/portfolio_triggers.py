from ..utils import get_active_assets


def generate_portfolio_triggers(
    weights,
    risk_contributions,
    concentration,
    diversification_ratio,
    portfolio_volatility,
    max_volatility=None,
    max_weight_constraint=0.35,
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

    total_abs_risk = sum(abs(v) for v in risk_contributions.values())

    # -------------------------
    # weight constraint
    # -------------------------

    for ticker, weight in sorted_weights:

        if weight >= max_weight_constraint - 0.01:

            items.append(
                {
                    "kind": "weight_constraint",
                    "asset": ticker,
                    "priority": 100,
                    "message": (
                        f"Watch {ticker}: the weight constraint is nearly binding. "
                        f"If its allocation increases further, rebalance toward the target allocation."
                    ),
                }
            )

            break

    # -------------------------
    # risk contribution
    # -------------------------

    if total_abs_risk > 0:

        ranked = sorted(
            risk_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        for ticker, rc in ranked:

            if ticker not in active_assets:
                continue

            share = abs(rc) / total_abs_risk

            if share >= 0.30:

                items.append(
                    {
                        "kind": "risk_contribution",
                        "asset": ticker,
                        "priority": 90,
                        "message": (
                            f"Watch {ticker}: its risk contribution is high. "
                            f"If its volatility increases further, total portfolio volatility may rise materially."
                        ),
                    }
                )

                break

    # -------------------------
    # negative risk contribution
    # -------------------------

    negative = [
        (t, rc)
        for t, rc in risk_contributions.items()
        if rc < 0 and t in active_assets
    ]

    if negative:

        ticker, rc = sorted(negative, key=lambda x: x[1])[0]

        items.append(
            {
                "kind": "risk_offset",
                "asset": ticker,
                "priority": 70,
                "message": (
                    f"Watch {ticker}: it currently has negative risk contribution and reduces portfolio volatility. "
                    f"If this effect weakens, recompute the portfolio."
                ),
            }
        )

    # -------------------------
    # concentration
    # -------------------------

    if concentration > 0.25:

        items.append(
            {
                "kind": "concentration",
                "asset": None,
                "priority": 80,
                "message": (
                    "Watch concentration: the portfolio is already concentrated. "
                    "If allocation becomes more uneven, rebalance."
                ),
            }
        )

    # -------------------------
    # diversification ratio
    # -------------------------

    if diversification_ratio < 1.2:

        items.append(
            {
                "kind": "diversification",
                "asset": None,
                "priority": 60,
                "message": (
                    "Watch diversification: the diversification ratio is low. "
                    "If volatility increases, review the portfolio structure."
                ),
            }
        )

    # -------------------------
    # volatility constraint
    # -------------------------

    if max_volatility is not None and max_volatility > 0:

        if portfolio_volatility >= 0.9 * max_volatility:

            items.append(
                {
                    "kind": "volatility_constraint",
                    "asset": None,
                    "priority": 95,
                    "message": (
                        "Watch volatility: portfolio volatility is close to the downside limit. "
                        "If volatility rises further, reduce higher-volatility allocations."
                    ),
                }
            )

    return items