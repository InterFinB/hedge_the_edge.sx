from .utils import get_top_positive_risk_contributors


def generate_risk_commentary(weights, risk_contributions):
    bullets = []

    top_positive = get_top_positive_risk_contributors(risk_contributions, top_n=2)

    if top_positive:
        names = ", ".join([ticker for ticker, _ in top_positive])
        if len(top_positive) == 1:
            bullets.append(f"The main source of portfolio risk is {names}.")
        else:
            bullets.append(f"The main sources of portfolio risk are {names}.")

    largest_weight_asset = None
    largest_weight_value = 0.0

    for ticker, weight in weights.items():
        if weight > largest_weight_value:
            largest_weight_asset = ticker
            largest_weight_value = weight

    if largest_weight_asset is not None and largest_weight_value >= 0.25:
        bullets.append(
            f"{largest_weight_asset} is one of the dominant positions in the portfolio, so changes in that asset can have a disproportionate impact on risk."
        )

    return bullets