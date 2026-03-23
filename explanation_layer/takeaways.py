from .utils import classify_concentration, classify_diversification, get_top_positive_risk_contributors


def generate_takeaways(
    concentration,
    diversification_ratio,
    risk_contributions,
    simulation_loss_probability=None,
):
    bullets = []

    conc_level = classify_concentration(concentration)
    div_level = classify_diversification(diversification_ratio)
    top_risk = get_top_positive_risk_contributors(risk_contributions, top_n=1)

    if div_level == "strong":
        bullets.append("Diversification is strong overall.")
    elif div_level == "moderate":
        bullets.append("Diversification is decent, but not especially strong.")
    else:
        bullets.append("Diversification is limited.")

    if conc_level == "high":
        bullets.append("The portfolio is fairly concentrated.")
    elif conc_level == "moderate":
        bullets.append("The portfolio still leans on a few larger positions.")
    else:
        bullets.append("No small group of holdings dominates the portfolio.")

    if top_risk:
        bullets.append(f"The biggest risk driver is {top_risk[0][0]}.")

    if simulation_loss_probability is not None:
        if simulation_loss_probability > 0.25:
            bullets.append("Modeled downside risk is meaningful.")
        elif simulation_loss_probability < 0.10:
            bullets.append("Modeled downside risk looks relatively contained.")

    return bullets[:3]