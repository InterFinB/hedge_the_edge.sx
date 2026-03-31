from .utils import (
    get_top_positive_risk_contributors,
    get_top_weights,
    format_asset_label,
    get_asset_category,
)


def generate_risk_commentary(weights, risk_contributions):
    bullets = []

    top_positive = get_top_positive_risk_contributors(risk_contributions, top_n=3)

    if top_positive:
        labels = [format_asset_label(ticker) for ticker, _ in top_positive]
        if len(labels) == 1:
            bullets.append(f"The main source of portfolio risk is {labels[0]}.")
        elif len(labels) == 2:
            bullets.append(f"The main sources of portfolio risk are {labels[0]} and {labels[1]}.")
        else:
            bullets.append(
                f"The main sources of portfolio risk are {labels[0]}, {labels[1]}, and {labels[2]}."
            )

    top_weights = get_top_weights(weights, top_n=1)
    if top_weights:
        largest_weight_asset, largest_weight_value = top_weights[0]
        if largest_weight_value >= 0.25:
            bullets.append(
                f"{format_asset_label(largest_weight_asset)} is a dominant position, so changes in that asset can have a disproportionate influence on portfolio risk."
            )

    if top_positive:
        lead_ticker = top_positive[0][0]
        lead_category = get_asset_category(lead_ticker)
        bullets.append(
            f"The leading risk contributor currently comes from the {lead_category} bucket."
        )

    return bullets[:3]