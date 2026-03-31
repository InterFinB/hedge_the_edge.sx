from .utils import (
    classify_concentration,
    classify_diversification,
    classify_loss_probability,
    classify_dispersion,
    classify_tail_severity,
    get_risk_share_profile,
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
    tail_level = classify_tail_severity(simulation_percentile_5)

    risk_profile = get_risk_share_profile(risk_contributions)
    top = risk_profile["top"]
    profile = risk_profile["profile"]

    # 1. Risk concentration logic
    if profile == "single_name_dominant" and top:
        bullets.append(
            f"Watch {format_asset_label(top[0][0])}: it is currently the single dominant driver of portfolio risk."
        )
    elif profile == "top_two_concentrated" and len(top) >= 2:
        bullets.append(
            f"Watch {format_asset_label(top[0][0])} and {format_asset_label(top[1][0])}: together they account for a concentrated share of total portfolio risk."
        )
    elif profile == "clustered" and len(top) >= 3:
        bullets.append(
            f"Watch {format_asset_label(top[0][0])}, {format_asset_label(top[1][0])}, and {format_asset_label(top[2][0])}: portfolio risk is clustered across these positions."
        )
    elif profile == "distributed":
        bullets.append(
            "Watch cross-asset interactions rather than a single name: portfolio risk is relatively distributed across multiple positions."
        )

    # 2. Structural portfolio quality
    if conc_level == "high":
        bullets.append(
            "Watch concentration closely: a small number of positions now account for a large share of portfolio behavior."
        )
    elif div_level == "low":
        bullets.append(
            "Watch diversification quality: portfolio-level risk reduction is limited, so correlation changes matter more."
        )

    # 3. Downside probability
    if downside_level == "elevated":
        bullets.append(
            "Pay close attention to downside risk: the modeled probability of a negative 1-year outcome is materially elevated."
        )
    elif downside_level == "moderate":
        bullets.append(
            "Watch downside conditions: if loss probability rises further, the portfolio may require more frequent rebalancing to maintain the target return."
        )
    elif downside_level == "low":
        bullets.append(
            "Keep an eye on downside conditions, even though modeled loss probability is relatively contained."
        )

    # 4. Tail severity
    if tail_level == "severe":
        bullets.append(
            f"Watch tail risk: the 5th-percentile outcome is {simulation_percentile_5:.2%}, which signals a severe downside tail under adverse scenarios."
        )
    elif tail_level == "meaningful":
        bullets.append(
            f"Watch downside dispersion: the 5th-percentile outcome reaches {simulation_percentile_5:.2%}."
        )

    # 5. Dispersion logic
    if dispersion_level == "wide":
        bullets.append(
            "Watch outcome dispersion: the simulated range is wide, so realized returns may vary materially from the central case."
        )
    elif dispersion_level == "moderate":
        bullets.append(
            "Watch scenario sensitivity: wider dispersion means realized returns may deviate more from expectations, especially in unstable markets."
        )

    # 6. Volatility-cap awareness
    if max_volatility is not None and portfolio_volatility is not None:
        if portfolio_volatility >= max_volatility * 0.95:
            bullets.append(
                f"Watch the volatility cap: current portfolio volatility ({portfolio_volatility:.2%}) is close to the requested limit ({max_volatility:.2%})."
            )

    # 7. Recompute cadence
    if portfolio_volatility is not None:
        schedule = get_recompute_schedule(portfolio_volatility)
        bullets.append(
            f"Watch for drift between recomputations: changes in volatility or correlations can gradually shift the portfolio away from its optimal structure."
        )

    if not bullets:
        bullets.append(
            "Watch the largest positions and leading risk contributors, as they are the fastest channels through which portfolio behavior can change."
        )
        bullets.append(
            "Watch simulation-based downside metrics over time, especially loss probability and the lower-tail outcome range."
        )

    deduped = []
    seen = set()
    for bullet in bullets:
        key = bullet.strip().lower()
        if key not in seen:
            deduped.append(bullet)
            seen.add(key)

    return deduped[:5]