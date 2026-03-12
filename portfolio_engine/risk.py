import numpy as np
from portfolio_engine.covariance import compute_covariance_matrix
from portfolio_engine.returns import compute_expected_returns


def compute_portfolio_volatility(weights, price_data):
    cov_matrix = compute_covariance_matrix(price_data)

    w = np.array(list(weights.values()))
    volatility = np.sqrt(w.T @ cov_matrix.values @ w)

    return volatility


def compute_portfolio_return(weights, price_data):
    mu = compute_expected_returns(price_data)

    w = np.array(list(weights.values()))
    portfolio_return = w.T @ mu.values

    return portfolio_return