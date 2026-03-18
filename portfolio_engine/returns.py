import numpy as np
import pandas as pd
from pypfopt import expected_returns

from portfolio_engine.config import (
    EXPECTED_RETURN_METHOD,
    EXPECTED_RETURN_BLEND_WEIGHT,
    EXPECTED_RETURN_SPAN,
    EXPECTED_RETURN_SIGNAL_WEIGHT,
    MIN_EXPECTED_RETURN,
    MAX_EXPECTED_RETURN,
    BASELINE_EXPECTED_RETURN,
    CATEGORY_BASELINE_RETURNS,
    TICKER_TO_CATEGORY,
)


def _sanitize_series(mu: pd.Series, index: pd.Index) -> pd.Series:
    """
    Force numeric dtype, preserve index, and replace inf with NaN.
    """
    mu = pd.Series(mu, index=index, dtype="float64")
    mu = mu.replace([np.inf, -np.inf], np.nan)
    return mu


def _clip_expected_returns(mu: pd.Series) -> pd.Series:
    return mu.clip(lower=MIN_EXPECTED_RETURN, upper=MAX_EXPECTED_RETURN)


def compute_historical_expected_returns(price_data: pd.DataFrame) -> pd.Series:
    mu = expected_returns.mean_historical_return(price_data)
    mu = _sanitize_series(mu, price_data.columns)
    mu = mu.fillna(BASELINE_EXPECTED_RETURN)
    return _clip_expected_returns(mu)


def compute_exponential_expected_returns(
    price_data: pd.DataFrame,
    span: int = EXPECTED_RETURN_SPAN,
) -> pd.Series:
    mu_exp = expected_returns.ema_historical_return(price_data, span=span)
    mu_exp = _sanitize_series(mu_exp, price_data.columns)

    # fallback 1: historical mean
    mu_hist = expected_returns.mean_historical_return(price_data)
    mu_hist = _sanitize_series(mu_hist, price_data.columns)

    # fallback 2: baseline
    mu = mu_exp.fillna(mu_hist)
    mu = mu.fillna(BASELINE_EXPECTED_RETURN)

    return _clip_expected_returns(mu)


def compute_baseline_expected_returns(price_data: pd.DataFrame) -> pd.Series:
    return pd.Series(
        BASELINE_EXPECTED_RETURN,
        index=price_data.columns,
        dtype=float,
    )


def compute_blended_expected_returns(
    price_data: pd.DataFrame,
    blend_weight: float = EXPECTED_RETURN_BLEND_WEIGHT,
    span: int = EXPECTED_RETURN_SPAN,
) -> pd.Series:
    if not 0 <= blend_weight <= 1:
        raise ValueError("blend_weight must be between 0 and 1.")

    mu_exp = compute_exponential_expected_returns(price_data, span=span)
    mu_base = compute_baseline_expected_returns(price_data)

    mu = blend_weight * mu_exp + (1 - blend_weight) * mu_base
    mu = _sanitize_series(mu, price_data.columns)
    mu = mu.fillna(BASELINE_EXPECTED_RETURN)

    return _clip_expected_returns(mu)


def compute_category_anchor_expected_returns(price_data: pd.DataFrame) -> pd.Series:
    """
    Build a deterministic equilibrium-style anchor return vector based on
    each asset's configured category.

    Any asset missing category metadata or a category-level anchor falls back
    to BASELINE_EXPECTED_RETURN.
    """
    anchor_values = {}

    for ticker in price_data.columns:
        category = TICKER_TO_CATEGORY.get(ticker)
        anchor_return = CATEGORY_BASELINE_RETURNS.get(
            category,
            BASELINE_EXPECTED_RETURN,
        )
        anchor_values[ticker] = float(anchor_return)

    mu_anchor = pd.Series(anchor_values, index=price_data.columns, dtype=float)
    mu_anchor = _sanitize_series(mu_anchor, price_data.columns)
    mu_anchor = mu_anchor.fillna(BASELINE_EXPECTED_RETURN)

    return _clip_expected_returns(mu_anchor)


def compute_equilibrium_blended_expected_returns(
    price_data: pd.DataFrame,
    signal_weight: float = EXPECTED_RETURN_SIGNAL_WEIGHT,
    span: int = EXPECTED_RETURN_SPAN,
) -> pd.Series:
    """
    Blend the current deterministic signal model with a category-based
    equilibrium anchor.

    final_mu = signal_weight * signal_mu + (1 - signal_weight) * anchor_mu
    """
    if not 0 <= signal_weight <= 1:
        raise ValueError("signal_weight must be between 0 and 1.")

    mu_signal = compute_blended_expected_returns(
        price_data=price_data,
        blend_weight=EXPECTED_RETURN_BLEND_WEIGHT,
        span=span,
    )
    mu_anchor = compute_category_anchor_expected_returns(price_data)

    mu = signal_weight * mu_signal + (1 - signal_weight) * mu_anchor
    mu = _sanitize_series(mu, price_data.columns)
    mu = mu.fillna(BASELINE_EXPECTED_RETURN)

    return _clip_expected_returns(mu)


def compute_expected_returns(price_data: pd.DataFrame) -> pd.Series:
    method = EXPECTED_RETURN_METHOD.lower()

    if method == "historical":
        return compute_historical_expected_returns(price_data)

    if method == "exponential":
        return compute_exponential_expected_returns(price_data)

    if method == "blended":
        return compute_blended_expected_returns(price_data)

    if method == "equilibrium_blended":
        return compute_equilibrium_blended_expected_returns(price_data)

    raise ValueError(
        f"Unsupported EXPECTED_RETURN_METHOD: {EXPECTED_RETURN_METHOD}. "
        "Use 'historical', 'exponential', 'blended', or 'equilibrium_blended'."
    )