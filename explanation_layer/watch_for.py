from .utils import (
    classify_concentration,
    classify_diversification,
    classify_loss_probability,
    classify_dispersion,
    get_top_positive_risk_contributors,
    format_asset_label,
)
from portfolio_engine.recompute_schedule import get_recompute_schedule


def generate_watch_for(
    weights,
    risk_contributions,
    concentration,
    diversification_ratio,
    portfolio_volatility,
    expected_portfolio_return,
    simulation_loss_probability=None,
    simulation_percentile_5=None,
    simulation_percentile_95=None,
    max_volatility=None,
    max_weight_constraint=0.35,
):
    bullets = []

    conc_level = classify_concentration(concentration)
    div_level = classify_diversification(diversification_ratio)
    downside_level = classify_loss_probability(simulation_loss_probability)
    dispersion_level = classify_dispersion(
        simulation_percentile_5,
        simulation_percentile_95,
    )

    top_risk = get_top_positive_risk_contributors(risk_contributions, top_n=2)

    # 1. Risk-driver monitoring
    if top_risk:
        if len(top_risk) == 1:
            bullets.append(
                f"Watch {format_asset_label(top_risk[0][0])}: it is currently the main driver of portfolio risk."
            )
        else:
            bullets.append(
                f"Watch {format_asset_label(top_risk[0][0])} and {format_asset_label(top_risk[1][0])}: they are the leading contributors to portfolio risk."
            )

    # 2. Concentration / diversification
    if conc_level == "high":
        bullets.append(
            "Watch concentration closely: a small number of positions now account for a large share of portfolio behavior."
        )
    elif div_level == "low":
        bullets.append(
            "Watch diversification quality: portfolio risk reduction is limited, so correlations matter more."
        )

    # 3. Downside probability
    if downside_level == "elevated":
        bullets.append(
            "Watch downside risk: the modeled probability of a negative 1-year outcome is materially elevated."
        )
    elif downside_level == "moderate":
        bullets.append(
            "Watch downside conditions: modeled loss probability is not extreme, but it is high enough to matter in weaker markets."
        )

    # 4. Left-tail severity
    if simulation_percentile_5 is not None:
        if simulation_percentile_5 <= -0.10:
            bullets.append(
                f"Watch tail risk: the 5th-percentile outcome is {simulation_percentile_5:.2%}, which signals a meaningful downside tail."
            )
        elif simulation_percentile_5 <= -0.05:
            bullets.append(
                f"Watch downside dispersion: the 5th-percentile outcome reaches {simulation_percentile_5:.2%}."
            )

    # 5. Range width / dispersion
    if dispersion_level == "wide":
        bullets.append(
            "Watch outcome dispersion: the simulated range is wide, so realized returns may vary materially from the central case."
        )
    elif dispersion_level == "moderate":
        bullets.append(
            "Watch scenario sensitivity: the simulation range still implies meaningful uncertainty around expected outcomes."
        )

    # 6. Volatility-cap awareness
    if max_volatility is not None and portfolio_volatility is not None:
        if portfolio_volatility >= max_volatility * 0.95:
            bullets.append(
                f"Watch the volatility cap: current portfolio volatility ({portfolio_volatility:.2%}) is close to the requested limit ({max_volatility:.2%})."
            )

    # 7. Recompute cadence reminder in more intelligent form
    if portfolio_volatility is not None:
        schedule = get_recompute_schedule(portfolio_volatility)
        bullets.append(
            f"Watch for drift between recomputations: at the current volatility regime, the portfolio should be reviewed on roughly a {schedule.interval_label} cadence."
        )

    # Fallback: never return empty
    if not bullets:
        bullets.append(
            "Watch the largest positions and leading risk contributors, as they are the fastest channels through which portfolio behavior can change."
        )
        bullets.append(
            "Watch simulation-based downside metrics over time, especially loss probability and the lower-tail outcome range."
        )

    # Keep the section tight
    deduped = []
    seen = set()
    for bullet in bullets:
        key = bullet.strip().lower()
        if key not in seen:
            deduped.append(bullet)
            seen.add(key)

    return deduped[:5]