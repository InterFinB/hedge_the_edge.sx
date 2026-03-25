import numpy as np


def compute_portfolio_volatility(weights, cov_matrix):
    """
    Compute annualized portfolio volatility using a precomputed covariance matrix
    and only the assets present in the supplied weights dictionary.
    """
    assets = list(weights.keys())
    w = np.array([weights[a] for a in assets], dtype=float)
    cov = cov_matrix.loc[assets, assets].values

    volatility = np.sqrt(w.T @ cov @ w)

    return float(volatility)


def compute_portfolio_return(weights, expected_returns):
    """
    Compute expected portfolio return using a precomputed expected return vector
    and only the assets present in the supplied weights dictionary.
    """
    assets = list(weights.keys())
    w = np.array([weights[a] for a in assets], dtype=float)
    mu_vector = expected_returns.loc[assets].values

    portfolio_return = w.T @ mu_vector

    return float(portfolio_return)