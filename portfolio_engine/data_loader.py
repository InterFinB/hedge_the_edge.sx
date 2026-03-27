import yfinance as yf
import pandas as pd
import datetime
import time

from portfolio_engine.config import TICKERS, START_DATE
from portfolio_engine.returns import compute_expected_returns
from portfolio_engine.covariance import compute_covariance_matrix


_cached_price_data = None
_cached_expected_returns = None
_cached_cov_matrix = None
_cached_tickers = None
_cache_timestamp = None

CACHE_TTL_SECONDS = 3600  # 1 hour
DOWNLOAD_RETRIES = 3
RETRY_SLEEP_SECONDS = 5


def _is_cache_valid() -> bool:
    global _cache_timestamp

    if _cache_timestamp is None:
        return False

    age = (datetime.datetime.now() - _cache_timestamp).total_seconds()
    return age < CACHE_TTL_SECONDS


def _extract_price_frame(raw: pd.DataFrame) -> pd.DataFrame:
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


def _download_and_prepare_price_data() -> pd.DataFrame:
    end_date = datetime.datetime.today()
    last_error = None

    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            raw = yf.download(
                TICKERS,
                start=START_DATE,
                end=end_date,
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            return _extract_price_frame(raw)

        except Exception as e:
            last_error = e

            if attempt < DOWNLOAD_RETRIES:
                time.sleep(RETRY_SLEEP_SECONDS)

    raise ValueError(f"Failed to download price data after {DOWNLOAD_RETRIES} attempts: {last_error}")


def _build_market_state(price_data: pd.DataFrame) -> dict:
    expected_returns = compute_expected_returns(price_data)
    cov_matrix = compute_covariance_matrix(price_data)
    tickers = list(price_data.columns)

    return {
        "price_data": price_data,
        "expected_returns": expected_returns,
        "cov_matrix": cov_matrix,
        "tickers": tickers,
    }


def _store_cache(price_data: pd.DataFrame, expected_returns, cov_matrix, tickers) -> None:
    global _cached_price_data
    global _cached_expected_returns
    global _cached_cov_matrix
    global _cached_tickers
    global _cache_timestamp

    _cached_price_data = price_data
    _cached_expected_returns = expected_returns
    _cached_cov_matrix = cov_matrix
    _cached_tickers = tickers
    _cache_timestamp = datetime.datetime.now()


def refresh_market_cache(force_refresh: bool = False) -> dict:
    global _cached_price_data
    global _cached_expected_returns
    global _cached_cov_matrix
    global _cached_tickers
    global _cache_timestamp

    has_any_cache = (
        _cached_price_data is not None
        and _cached_expected_returns is not None
        and _cached_cov_matrix is not None
        and _cached_tickers is not None
        and _cache_timestamp is not None
    )

    if not force_refresh and has_any_cache and _is_cache_valid():
        return {
            "price_data": _cached_price_data,
            "expected_returns": _cached_expected_returns,
            "cov_matrix": _cached_cov_matrix,
            "tickers": _cached_tickers,
            "cache_timestamp": _cache_timestamp,
            "cache_status": "fresh",
        }

    try:
        price_data = _download_and_prepare_price_data()
        market_state = _build_market_state(price_data)

        _store_cache(
            price_data=market_state["price_data"],
            expected_returns=market_state["expected_returns"],
            cov_matrix=market_state["cov_matrix"],
            tickers=market_state["tickers"],
        )

        return {
            "price_data": _cached_price_data,
            "expected_returns": _cached_expected_returns,
            "cov_matrix": _cached_cov_matrix,
            "tickers": _cached_tickers,
            "cache_timestamp": _cache_timestamp,
            "cache_status": "fresh",
        }

    except Exception as e:
        if has_any_cache:
            return {
                "price_data": _cached_price_data,
                "expected_returns": _cached_expected_returns,
                "cov_matrix": _cached_cov_matrix,
                "tickers": _cached_tickers,
                "cache_timestamp": _cache_timestamp,
                "cache_status": "stale_fallback",
                "warning": f"Using stale cached market data because refresh failed: {e}",
            }

        raise ValueError(
            f"Unable to load market data and no cached data is available. Original error: {e}"
        )


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