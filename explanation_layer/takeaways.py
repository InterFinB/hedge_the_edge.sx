from .utils import (
    classify_concentration,
    classify_diversification,
    get_top_positive_risk_contributors,
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
    top_risk = get_top_positive_risk_contributors(risk_contributions, top_n=1)

    if div_level == "strong":
        bullets.append("Diversification is strong at the portfolio level.")
    elif div_level == "moderate":
        bullets.append("Diversification is moderate.")
    else:
        bullets.append("Diversification is limited.")

    if conc_level == "high":
        bullets.append("Concentration is elevated.")
    elif conc_level == "moderate":
        bullets.append("Concentration is noticeable but not extreme.")
    else:
        bullets.append("Concentration is low.")

    if portfolio_volatility is not None and desired_return is not None:
        schedule = get_recompute_schedule(portfolio_volatility)
        bullets.append(
            f"To maintain the target return of {format_pct(desired_return)} on a minimum-risk basis, "
            f"the portfolio should be recomputed every {schedule.interval_label}."
        )

    if top_risk:
        bullets.append(f"The main risk contribution comes from {top_risk[0][0]}.")

    if simulation_loss_probability is not None:
        if simulation_loss_probability > 0.25:
            bullets.append("Modeled downside risk is materially elevated.")
        elif simulation_loss_probability < 0.10:
            bullets.append("Modeled downside risk is relatively contained.")

    return bullets[:4]