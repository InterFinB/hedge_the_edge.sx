from .utils import get_active_assets, get_top_positive_risk_contributors, find_capped_assets


def generate_watch_for(weights, risk_contributions, max_weight_constraint=0.35):
    bullets = []

    active_assets = get_active_assets(weights)
    top_weight_assets = sorted(active_assets.items(), key=lambda x: x[1], reverse=True)[:2]
    top_risk_assets = get_top_positive_risk_contributors(risk_contributions, top_n=2)
    capped_assets = set(find_capped_assets(weights, max_weight_constraint=max_weight_constraint))

    seen = set()

    for asset, weight in top_weight_assets:
        if asset in seen:
            continue

        if asset in capped_assets:
            bullets.append(
                f"Watch {asset}: it already reached the weight cap, so the portfolio depends heavily on it."
            )
        else:
            bullets.append(
                f"Watch {asset}: it is one of the largest holdings, so big moves here can noticeably affect results."
            )
        seen.add(asset)

    for asset, rc in top_risk_assets:
        if asset in seen:
            continue
        bullets.append(
            f"Watch {asset}: it is one of the main risk drivers, so higher volatility here could raise overall portfolio risk."
        )
        seen.add(asset)

    return bullets[:2]