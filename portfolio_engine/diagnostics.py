import numpy as np
from portfolio_engine.covariance import compute_covariance_matrix


def compute_risk_contributions(weights, price_data):
    """
    Compute each asset's contribution to portfolio volatility.
    Returns a dictionary {asset: contribution}.
    """
    cov_matrix = compute_covariance_matrix(price_data)

    assets = list(weights.keys())
    w = np.array(list(weights.values()), dtype=float)
    cov = cov_matrix.loc[assets, assets].values

    portfolio_var = w.T @ cov @ w
    portfolio_vol = np.sqrt(portfolio_var)

    if portfolio_vol == 0:
        return {asset: 0.0 for asset in assets}

    marginal_contrib = cov @ w
    risk_contrib = w * marginal_contrib / portfolio_vol

    return dict(zip(assets, risk_contrib))


def compute_concentration(weights):
    """
    Herfindahl concentration index.
    Higher = more concentrated portfolio.
    """
    w = np.array(list(weights.values()), dtype=float)
    return float(np.sum(w ** 2))


def compute_diversification_ratio(weights, price_data):
    """
    Diversification ratio:
    weighted average asset volatility / portfolio volatility
    """
    cov_matrix = compute_covariance_matrix(price_data)

    assets = list(weights.keys())
    w = np.array(list(weights.values()), dtype=float)
    cov = cov_matrix.loc[assets, assets].values

    portfolio_vol = np.sqrt(w.T @ cov @ w)

    if portfolio_vol == 0:
        return 0.0

    asset_vols = np.sqrt(np.diag(cov))
    weighted_asset_vol = np.sum(w * asset_vols)

    return float(weighted_asset_vol / portfolio_vol)