from .utils import (
    classify_concentration,
    classify_diversification,
    classify_loss_probability,
    get_risk_share_profile,
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
    risk_profile = get_risk_share_profile(risk_contributions)

    top = risk_profile["top"]
    profile = risk_profile["profile"]

    # 1. Structural summary of the portfolio
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

    # 2. Dynamic risk concentration summary
    if profile == "single_name_dominant" and top:
        bullets.append(
            f"{format_asset_label(top[0][0])} is currently the single largest driver of portfolio risk."
        )
    elif profile == "top_two_concentrated" and len(top) >= 2:
        bullets.append(
            f"Risk is concentrated primarily in {format_asset_label(top[0][0])} and {format_asset_label(top[1][0])}."
        )
    elif profile == "clustered" and len(top) >= 3:
        bullets.append(
            "Risk is concentrated in a small cluster of positions rather than being dominated by only one name."
        )
    elif profile == "distributed":
        bullets.append(
            "Risk is distributed across several positions rather than being dominated by a single name."
        )

    # 3. Recompute cadence
    if portfolio_volatility is not None and desired_return is not None:
        schedule = get_recompute_schedule(portfolio_volatility)
        bullets.append(
            f"To maintain the target return of {format_pct(desired_return)} on a minimum-risk basis, the portfolio should be recomputed every {schedule.interval_label}."
        )

    # 4. Downside framing
    if downside_level == "elevated":
        bullets.append(
            "Modeled downside risk is materially elevated and should be weighed against return objectives."
        )
    elif downside_level == "low":
        bullets.append(
            "Modeled downside risk is relatively contained."
        )

    return bullets[:5]