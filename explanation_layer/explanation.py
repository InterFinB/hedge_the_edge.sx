def generate_explanation(
    desired_return,
    expected_portfolio_return,
    portfolio_volatility,
    weights,
    feasible=None,
    max_weight_constraint=0.35
):
    """
    Generate a financially richer human-readable explanation
    of the portfolio recommendation.
    """

    # Assets that are actually used
    active_assets = {k: v for k, v in weights.items() if v > 0.001}

    # Assets effectively excluded
    zero_weight_assets = [k for k, v in weights.items() if v <= 0.001]

    # Sort by descending weight
    sorted_assets = sorted(active_assets.items(), key=lambda x: x[1], reverse=True)

    top_assets = sorted_assets[:3]
    top_text = ", ".join([f"{asset} ({weight:.1%})" for asset, weight in top_assets])

    explanation_parts = []

    # Core portfolio description
    explanation_parts.append(
        f"To achieve the requested return of {desired_return:.2%}, the model constructed "
        f"a portfolio with an expected return of {expected_portfolio_return:.2%} and an "
        f"estimated volatility of {portfolio_volatility:.2%}."
    )

    # Top allocations
    if top_assets:
        explanation_parts.append(
            f"The largest allocations were made to {top_text}, because these assets "
            f"offered the most efficient contribution to the portfolio's return-risk trade-off "
            f"under the optimization constraints."
        )

    # Asset role classification
    defensive_assets = []
    growth_assets = []
    diversifiers = []

    for asset in active_assets.keys():
        if asset in ["AGG", "TLT", "LQD"]:
            defensive_assets.append(asset)
        elif asset in ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "SPY", "QQQ"]:
            growth_assets.append(asset)
        elif asset in ["GLD", "DBC", "XLV", "VNQ", "VEA", "VWO"]:
            diversifiers.append(asset)

    if defensive_assets:
        explanation_parts.append(
            f"Defensive assets such as {', '.join(defensive_assets)} help reduce total "
            f"portfolio volatility and stabilize the allocation."
        )

    if diversifiers:
        explanation_parts.append(
            f"Diversifying assets such as {', '.join(diversifiers)} improve stability by "
            f"adding exposure to different sectors or market drivers, which reduces dependence "
            f"on a single source of return."
        )

    if growth_assets:
        explanation_parts.append(
            f"Growth-oriented exposure through {', '.join(growth_assets)} helps the portfolio "
            f"reach the desired return target."
        )

    # Explain excluded assets
    if zero_weight_assets:
        excluded_preview = ", ".join(zero_weight_assets[:5])
        explanation_parts.append(
            f"Some assets, such as {excluded_preview}, received zero or near-zero weight because "
            f"they did not improve the portfolio's return-risk balance enough under the current "
            f"market estimates and constraints."
        )

    # Explain concentration cap if binding
    capped_assets = [asset for asset, weight in active_assets.items() if abs(weight - max_weight_constraint) < 0.001]

    if capped_assets:
        explanation_parts.append(
            f"The allocation was also shaped by the maximum weight constraint of "
            f"{max_weight_constraint:.0%} per asset. This cap was binding for "
            f"{', '.join(capped_assets)}, which prevented the optimizer from concentrating "
            f"too heavily in a small number of low-risk assets."
        )

    # Feasibility / downside tolerance
    if feasible is True:
        explanation_parts.append(
            "The portfolio also satisfies the user's downside tolerance constraint, meaning "
            "the requested return is achievable within the selected risk limit."
        )
    elif feasible is False:
        explanation_parts.append(
            "However, the portfolio exceeds the user's downside tolerance, which means the "
            "requested return appears to require more risk than the user is comfortable accepting."
        )

    return " ".join(explanation_parts)