from .utils import (
    classify_concentration,
    classify_diversification,
    find_capped_assets,
    get_top_weights,
)


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

    bullets.append(
        f"Target return: {desired_return:.2%}. "
        f"Expected return: {expected_portfolio_return:.2%}. "
        f"Risk: {portfolio_volatility:.2%}."
    )

    if top_assets:
        top_alloc_text = ", ".join(
            f"{asset} ({weight:.1%})" for asset, weight in top_assets
        )
        bullets.append(f"Largest holdings: {top_alloc_text}.")

    div_level = classify_diversification(diversification_ratio)
    if div_level == "low":
        bullets.append(
            f"Diversification is limited ({diversification_ratio:.2f})."
        )
    elif div_level == "moderate":
        bullets.append(
            f"Diversification is moderate ({diversification_ratio:.2f})."
        )
    else:
        bullets.append(
            f"Diversification is strong ({diversification_ratio:.2f})."
        )

    conc_level = classify_concentration(concentration)
    if conc_level == "low":
        bullets.append(
            f"Concentration is low ({concentration:.3f})."
        )
    elif conc_level == "moderate":
        bullets.append(
            f"Concentration is moderate ({concentration:.3f}). A few holdings matter more than the rest."
        )
    else:
        bullets.append(
            f"Concentration is high ({concentration:.3f}). The portfolio depends heavily on a few positions."
        )

    capped_assets = find_capped_assets(weights, max_weight_constraint=max_weight_constraint)
    if capped_assets:
        bullets.append(
            f"Weight cap reached: {', '.join(capped_assets)} hit the {max_weight_constraint:.0%} limit."
        )

    return bullets[:5]