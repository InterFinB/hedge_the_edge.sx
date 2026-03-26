import yfinance as yf
import pandas as pd
import datetime

from portfolio_engine.config import TICKERS, START_DATE
from portfolio_engine.returns import compute_expected_returns
from portfolio_engine.covariance import compute_covariance_matrix


_cached_price_data = None
_cached_expected_returns = None
_cached_cov_matrix = None
_cached_tickers = None
_cache_timestamp = None

CACHE_TTL_SECONDS = 3600  # 1 hour


def _is_cache_valid() -> bool:
    global _cache_timestamp

    if _cache_timestamp is None:
        return False

    age = (datetime.datetime.now() - _cache_timestamp).total_seconds()
    return age < CACHE_TTL_SECONDS


def _download_and_prepare_price_data() -> pd.DataFrame:
    end_date = datetime.datetime.today()

    raw = yf.download(
        TICKERS,
        start=START_DATE,
        end=end_date,
        progress=False,
        auto_adjust=False,
    )

    if raw is None or raw.empty:
        raise ValueError("Yahoo Finance returned no data.")

    if isinstance(raw.columns, pd.MultiIndex):
        if "Adj Close" in raw.columns.levels[0]:
            data = raw["Adj Close"]
        elif "Close" in raw.columns.levels[0]:
            data = raw["Close"]
        else:
            raise ValueError("No price column found in Yahoo data.")
    else:
        if "Adj Close" in raw.columns:
            data = raw[["Adj Close"]]
        elif "Close" in raw.columns:
            data = raw[["Close"]]
        else:
            raise ValueError("No price column found in Yahoo data.")

    if data is None or data.empty:
        raise ValueError("Price data is empty after selecting price columns.")

    data = data.sort_index()
    data = data.ffill()

    threshold = int(len(data) * 0.8)
    data = data.dropna(axis=1, thresh=threshold)
    data = data.dropna()

    if data.empty:
        raise ValueError("Price data is empty after cleaning.")

    if data.shape[1] < 2:
        raise ValueError("Not enough valid price data after cleaning.")

    return data


def refresh_market_cache(force_refresh: bool = False) -> dict:
    global _cached_price_data
    global _cached_expected_returns
    global _cached_cov_matrix
    global _cached_tickers
    global _cache_timestamp

    if not force_refresh and _cached_price_data is not None and _is_cache_valid():
        return {
            "price_data": _cached_price_data,
            "expected_returns": _cached_expected_returns,
            "cov_matrix": _cached_cov_matrix,
            "tickers": _cached_tickers,
            "cache_timestamp": _cache_timestamp,
        }

    price_data = _download_and_prepare_price_data()
    expected_returns = compute_expected_returns(price_data)
    cov_matrix = compute_covariance_matrix(price_data)
    tickers = list(price_data.columns)

    _cached_price_data = price_data
    _cached_expected_returns = expected_returns
    _cached_cov_matrix = cov_matrix
    _cached_tickers = tickers
    _cache_timestamp = datetime.datetime.now()

    return {
        "price_data": _cached_price_data,
        "expected_returns": _cached_expected_returns,
        "cov_matrix": _cached_cov_matrix,
        "tickers": _cached_tickers,
        "cache_timestamp": _cache_timestamp,
    }


def load_price_data(force_refresh: bool = False) -> pd.DataFrame:
    return refresh_market_cache(force_refresh=force_refresh)["price_data"]


def load_market_state(force_refresh: bool = False) -> dict:
    return refresh_market_cache(force_refresh=force_refresh)


def get_cache_status() -> dict:
    return {
        "cache_valid": _is_cache_valid(),
        "cache_timestamp": _cache_timestamp.isoformat() if _cache_timestamp else None,
        "num_assets": len(_cached_tickers) if _cached_tickers is not None else 0,
        "tickers": _cached_tickers if _cached_tickers is not None else [],
    }


def force_refresh() -> dict:
    return refresh_market_cache(force_refresh=True)