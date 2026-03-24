from .utils import (
    get_negative_risk_contributors,
    get_top_positive_risk_contributors,
)


def generate_risk_commentary(weights, risk_contributions):
    bullets = []

    top_risk_assets = get_top_positive_risk_contributors(risk_contributions, top_n=3)
    negative_risk_assets = get_negative_risk_contributors(risk_contributions)

    if top_risk_assets:
        top_risk_text = ", ".join(asset for asset, _ in top_risk_assets)
        bullets.append(
            f"The largest contributors to portfolio volatility are {top_risk_text}."
        )

    if negative_risk_assets:
        preview = ", ".join(negative_risk_assets[:2])
        bullets.append(
            f"{preview} currently provides negative risk contribution and helps offset total portfolio volatility."
        )

    return bullets[:3]