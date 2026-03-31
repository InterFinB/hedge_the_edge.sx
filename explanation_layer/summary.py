from .utils import (
    classify_concentration,
    classify_diversification,
    find_capped_assets,
    get_top_weights,
    get_top_categories,
    format_asset_label,
)


def _classify_portfolio_style(top_categories):
    if not top_categories:
        return None

    categories = [category for category, _ in top_categories]

    defensive_set = {
        "Bond ETFs",
        "Alternative Assets",
        "Consumer Staples Stocks",
        "Health Care Stocks",
        "Utilities Stocks",
    }

    equity_growth_set = {
        "Technology Stocks",
        "Consumer Discretionary Stocks",
        "Communication Services Stocks",
        "Sector ETFs",
        "Broad Market ETFs",
    }

    defensive_count = sum(1 for c in categories if c in defensive_set)
    growth_count = sum(1 for c in categories if c in equity_growth_set)

    if defensive_count >= 2:
        return "defensive-diversified"
    if growth_count >= 2:
        return "growth-tilted"
    return "balanced"


def generate_portfolio_summary(
    desired_return,
    expected_portfolio_return,
    portfolio_volatility,
    weights,
    diversification_ratio,
    concentration,
    max_weight_constraint=0.35,
):
    bullets = []

    top_assets = get_top_weights(weights, top_n=3)
    top_categories = get_top_categories(weights, top_n=3)
    portfolio_style = _classify_portfolio_style(top_categories)

    bullets.append(
        f"Target return: {desired_return:.2%}. "
        f"Expected return: {expected_portfolio_return:.2%}. "
        f"Volatility: {portfolio_volatility:.2%}."
    )

    if top_assets:
        top_alloc_text = ", ".join(
            f"{format_asset_label(asset)} — {weight:.1%}"
            for asset, weight in top_assets
        )
        bullets.append(f"Largest allocations: {top_alloc_text}.")

    if top_categories:
        top_category_text = ", ".join(
            f"{category} ({weight:.1%})"
            for category, weight in top_categories
        )
        bullets.append(f"Largest category exposures: {top_category_text}.")

    if portfolio_style == "defensive-diversified":
        bullets.append(
            "The portfolio currently leans on defensive and diversifying categories rather than a single growth-heavy theme."
        )
    elif portfolio_style == "growth-tilted":
        bullets.append(
            "The portfolio currently leans more toward growth-oriented categories, which can support return targeting but may increase sensitivity to equity-market conditions."
        )
    elif portfolio_style == "balanced":
        bullets.append(
            "The portfolio is distributed across multiple category buckets without a single dominant style bias."
        )

    div_level = classify_diversification(diversification_ratio)
    conc_level = classify_concentration(concentration)

    if div_level == "low" and conc_level == "high":
        bullets.append(
            f"Diversification is weak ({diversification_ratio:.2f}) and concentration is high ({concentration:.3f}), so portfolio risk is not broadly spread."
        )
    elif div_level == "low":
        bullets.append(
            f"Diversification is weak ({diversification_ratio:.2f}), so portfolio-level risk reduction is limited."
        )
    elif div_level == "moderate":
        bullets.append(
            f"Diversification is moderate ({diversification_ratio:.2f})."
        )
    else:
        bullets.append(
            f"Diversification is strong ({diversification_ratio:.2f})."
        )

    if conc_level == "low":
        bullets.append(
            f"Concentration is low ({concentration:.3f})."
        )
    elif conc_level == "moderate":
        bullets.append(
            f"Concentration is moderate ({concentration:.3f}), so dependence on the largest positions is noticeable."
        )
    else:
        bullets.append(
            f"Concentration is high ({concentration:.3f}), so the portfolio depends heavily on a small number of positions."
        )

    capped_assets = find_capped_assets(
        weights,
        max_weight_constraint=max_weight_constraint,
    )
    if capped_assets:
        capped_text = ", ".join(format_asset_label(asset) for asset in capped_assets)
        bullets.append(
            f"Weight constraint is binding for {capped_text} at the {max_weight_constraint:.0%} maximum allocation."
        )

    return bullets[:6]