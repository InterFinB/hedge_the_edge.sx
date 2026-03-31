from .utils import (
    classify_concentration,
    classify_diversification,
    classify_loss_probability,
    get_top_positive_risk_contributors,
    get_top_categories,
    format_asset_label,
)
from portfolio_engine.recompute_schedule import get_recompute_schedule


def format_pct(value):
    return f"{value * 100:.1f}%"


def generate_takeaways(
    concentration,
    diversification_ratio,
    risk_contributions,
    simulation_loss_probability=None,
    portfolio_volatility=None,
    desired_return=None,
):
    bullets = []

    conc_level = classify_concentration(concentration)
    div_level = classify_diversification(diversification_ratio)
    downside_level = classify_loss_probability(simulation_loss_probability)
    top_risk = get_top_positive_risk_contributors(risk_contributions, top_n=1)

    # Build a more decision-useful summary of structure
    if div_level == "strong" and conc_level == "low":
        bullets.append(
            "The portfolio reaches its objective without relying on a single dominant position, which supports resilience at the portfolio level."
        )
    elif div_level == "moderate" and conc_level == "moderate":
        bullets.append(
            "The portfolio is reasonably spread, but its largest positions still matter for overall behavior."
        )
    elif div_level == "low":
        bullets.append(
            "Portfolio risk is not broadly distributed, so performance will depend more heavily on a narrower set of exposures."
        )
    else:
        bullets.append(
            "The portfolio structure is acceptable, but concentration and diversification should still be monitored together."
        )

    if conc_level == "high":
        bullets.append("Concentration is elevated and should be monitored closely.")
    elif conc_level == "moderate":
        bullets.append("Concentration is noticeable but not extreme.")
    else:
        bullets.append("Concentration is low.")

    if portfolio_volatility is not None and desired_return is not None:
        schedule = get_recompute_schedule(portfolio_volatility)
        bullets.append(
            f"To maintain the target return of {format_pct(desired_return)} on a minimum-risk basis, the portfolio should be recomputed every {schedule.interval_label}."
        )

    if top_risk:
        bullets.append(
            f"The largest current risk contribution comes from {format_asset_label(top_risk[0][0])}."
        )

    if downside_level == "elevated":
        bullets.append(
            "Modeled downside risk is materially elevated, so the target return should be evaluated against tolerance for negative outcomes."
        )
    elif downside_level == "low":
        bullets.append("Modeled downside risk is relatively contained.")

    return bullets[:5]