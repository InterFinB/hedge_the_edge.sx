from portfolio_engine.config import TICKER_TO_NAME, TICKER_TO_CATEGORY


def get_active_assets(weights, threshold=0.001):
    return {asset: weight for asset, weight in weights.items() if weight > threshold}


def get_zero_weight_assets(weights, threshold=0.001):
    return [asset for asset, weight in weights.items() if weight <= threshold]


def get_top_weights(weights, top_n=3, threshold=0.001):
    active_assets = get_active_assets(weights, threshold=threshold)
    return sorted(active_assets.items(), key=lambda x: x[1], reverse=True)[:top_n]


def get_top_positive_risk_contributors(risk_contributions, top_n=3):
    positive = [(asset, rc) for asset, rc in risk_contributions.items() if rc > 0]
    return sorted(positive, key=lambda x: x[1], reverse=True)[:top_n]


def get_negative_risk_contributors(risk_contributions):
    return [asset for asset, rc in risk_contributions.items() if rc < 0]


def classify_diversification(diversification_ratio):
    if diversification_ratio < 1.2:
        return "low"
    if diversification_ratio <= 1.5:
        return "moderate"
    return "strong"


def classify_concentration(concentration):
    if concentration < 0.15:
        return "low"
    if concentration <= 0.25:
        return "moderate"
    return "high"


def classify_loss_probability(loss_probability):
    if loss_probability is None:
        return None
    if loss_probability < 0.10:
        return "low"
    if loss_probability < 0.25:
        return "moderate"
    return "elevated"


def classify_dispersion(p5, p95):
    if p5 is None or p95 is None:
        return None

    spread = p95 - p5

    if spread < 0.15:
        return "tight"
    if spread < 0.30:
        return "moderate"
    return "wide"


def find_capped_assets(weights, max_weight_constraint, threshold=0.001):
    active_assets = get_active_assets(weights, threshold=threshold)
    return [
        asset
        for asset, weight in active_assets.items()
        if abs(weight - max_weight_constraint) < threshold
    ]


def get_asset_display_name(ticker):
    return TICKER_TO_NAME.get(ticker, ticker)


def get_asset_category(ticker):
    return TICKER_TO_CATEGORY.get(ticker, "Uncategorized")


def format_asset_label(ticker):
    name = get_asset_display_name(ticker)
    if name == ticker:
        return ticker
    return f"{ticker} ({name})"


def build_category_exposure(weights, threshold=0.001):
    active_assets = get_active_assets(weights, threshold=threshold)
    exposure = {}

    for ticker, weight in active_assets.items():
        category = get_asset_category(ticker)
        exposure[category] = exposure.get(category, 0.0) + float(weight)

    return sorted(exposure.items(), key=lambda x: x[1], reverse=True)


def get_top_categories(weights, top_n=3, threshold=0.001):
    return build_category_exposure(weights, threshold=threshold)[:top_n]


def asset_buckets(active_assets):
    defensive_assets = []
    growth_assets = []
    diversifiers = []
    defensive_equity = []
    cyclical_assets = []

    for asset in active_assets:
        if asset in ["AGG", "TLT", "LQD"]:
            defensive_assets.append(asset)

        if asset in ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "QQQ", "SPY", "IJR", "VWO"]:
            growth_assets.append(asset)

        if asset in ["GLD", "DBC", "VEA", "VNQ", "XLV", "XLF", "XLE", "XLI"]:
            diversifiers.append(asset)

        if asset in ["JNJ", "UNH", "XLV"]:
            defensive_equity.append(asset)

        if asset in ["XOM", "XLE", "DBC"]:
            cyclical_assets.append(asset)

    return {
        "defensive_assets": defensive_assets,
        "growth_assets": growth_assets,
        "diversifiers": diversifiers,
        "defensive_equity": defensive_equity,
        "cyclical_assets": cyclical_assets,
    }