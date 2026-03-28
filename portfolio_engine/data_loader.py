import datetime
import time
from typing import List, Tuple

import pandas as pd
import yfinance as yf

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
MIN_VALID_COLUMN_RATIO = 0.8
MIN_REQUIRED_ASSETS = 2


def _is_cache_valid() -> bool:
    global _cache_timestamp

    if _cache_timestamp is None:
        return False

    age = (datetime.datetime.now() - _cache_timestamp).total_seconds()
    return age < CACHE_TTL_SECONDS


def _normalize_to_dataframe(data: pd.DataFrame, requested_tickers: List[str]) -> pd.DataFrame:
    """
    Ensures the returned price frame is always a DataFrame whose columns are ticker symbols.
    """
    if data is None or data.empty:
        raise ValueError("Yahoo Finance returned no data.")

    if isinstance(data, pd.Series):
        ticker_name = requested_tickers[0] if requested_tickers else "UNKNOWN"
        data = data.to_frame(name=ticker_name)

    if not isinstance(data, pd.DataFrame):
        raise ValueError("Yahoo Finance returned an unexpected data format.")

    return data


def _extract_price_frame(raw: pd.DataFrame, requested_tickers: List[str]) -> pd.DataFrame:
    """
    Extracts Adj Close (preferred) or Close from Yahoo response and returns
    a normalized DataFrame with ticker columns.
    """
    if raw is None or raw.empty:
        raise ValueError("Yahoo Finance returned no data.")

    if isinstance(raw.columns, pd.MultiIndex):
        level0 = raw.columns.get_level_values(0)
        if "Adj Close" in level0:
            data = raw["Adj Close"]
        elif "Close" in level0:
            data = raw["Close"]
        else:
            raise ValueError("No price column found in Yahoo data.")
    else:
        if "Adj Close" in raw.columns:
            data = raw[["Adj Close"]].copy()
            if len(requested_tickers) == 1:
                data.columns = [requested_tickers[0]]
        elif "Close" in raw.columns:
            data = raw[["Close"]].copy()
            if len(requested_tickers) == 1:
                data.columns = [requested_tickers[0]]
        else:
            data = raw.copy()

    data = _normalize_to_dataframe(data, requested_tickers)
    data = data.sort_index()
    return data


def _download_raw_prices(requested_tickers: List[str]) -> pd.DataFrame:
    """
    Downloads raw Yahoo data with retries.
    """
    if not requested_tickers:
        raise ValueError("No tickers provided for download.")

    last_error = None
    end_date = datetime.datetime.today()

    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            raw = yf.download(
                requested_tickers,
                start=START_DATE,
                end=end_date,
                progress=False,
                auto_adjust=False,
                threads=False,
                group_by="column",
            )

            if raw is None or raw.empty:
                raise ValueError("Yahoo Finance returned empty data.")

            return raw

        except Exception as e:
            last_error = e
            if attempt < DOWNLOAD_RETRIES:
                time.sleep(RETRY_SLEEP_SECONDS)

    raise ValueError(
        f"Failed to download raw price data after {DOWNLOAD_RETRIES} attempts: {last_error}"
    )


def _download_price_frame(requested_tickers: List[str]) -> pd.DataFrame:
    raw = _download_raw_prices(requested_tickers)
    return _extract_price_frame(raw, requested_tickers)


def _find_missing_tickers(price_data: pd.DataFrame, requested_tickers: List[str]) -> List[str]:
    available = set(price_data.columns.tolist())
    return [ticker for ticker in requested_tickers if ticker not in available]


def _download_missing_tickers_individually(missing_tickers: List[str]) -> pd.DataFrame:
    """
    Attempts to recover failed tickers one by one. This helps when Yahoo partially
    rate-limits a batched request.
    """
    recovered_frames = []

    for ticker in missing_tickers:
        try:
            single_df = _download_price_frame([ticker])
            if ticker in single_df.columns:
                recovered_frames.append(single_df[[ticker]])
        except Exception:
            # We intentionally skip here; unrecovered tickers will simply remain missing.
            continue

    if not recovered_frames:
        return pd.DataFrame()

    combined = pd.concat(recovered_frames, axis=1)
    combined = combined.loc[:, ~combined.columns.duplicated()]
    combined = combined.sort_index()
    return combined


def _combine_price_frames(base: pd.DataFrame, recovered: pd.DataFrame) -> pd.DataFrame:
    if base is None or base.empty:
        return recovered.copy()

    if recovered is None or recovered.empty:
        return base.copy()

    combined = pd.concat([base, recovered], axis=1)
    combined = combined.loc[:, ~combined.columns.duplicated(keep="first")]
    combined = combined.sort_index()
    return combined


def _clean_price_data(price_data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Cleans the price frame and returns:
    - cleaned data
    - list of dropped tickers
    """
    if price_data is None or price_data.empty:
        raise ValueError("Price data is empty before cleaning.")

    data = price_data.copy()
    data = data.sort_index()
    data = data.ffill()

    min_non_null_count = max(1, int(len(data) * MIN_VALID_COLUMN_RATIO))
    kept_before_drop = list(data.columns)
    data = data.dropna(axis=1, thresh=min_non_null_count)
    dropped_tickers = [ticker for ticker in kept_before_drop if ticker not in data.columns]

    data = data.dropna()

    if data.empty:
        raise ValueError("Price data is empty after cleaning.")

    if data.shape[1] < MIN_REQUIRED_ASSETS:
        raise ValueError(
            f"Not enough valid assets after cleaning. "
            f"Need at least {MIN_REQUIRED_ASSETS}, got {data.shape[1]}."
        )

    return data, dropped_tickers


def _download_and_prepare_price_data() -> Tuple[pd.DataFrame, dict]:
    """
    Returns:
    - cleaned price_data
    - metadata about missing/dropped/recovered tickers
    """
    requested_tickers = list(TICKERS)

    initial_price_data = _download_price_frame(requested_tickers)
    missing_after_batch = _find_missing_tickers(initial_price_data, requested_tickers)

    recovered_data = pd.DataFrame()
    if missing_after_batch:
        recovered_data = _download_missing_tickers_individually(missing_after_batch)

    combined_price_data = _combine_price_frames(initial_price_data, recovered_data)

    still_missing = _find_missing_tickers(combined_price_data, requested_tickers)
    cleaned_price_data, dropped_after_cleaning = _clean_price_data(combined_price_data)

    metadata = {
        "requested_tickers": requested_tickers,
        "initial_missing_tickers": missing_after_batch,
        "recovered_tickers": [
            ticker for ticker in missing_after_batch if ticker in recovered_data.columns
        ],
        "final_missing_tickers": still_missing,
        "dropped_after_cleaning": dropped_after_cleaning,
        "final_tickers": list(cleaned_price_data.columns),
    }

    return cleaned_price_data, metadata


def _build_market_state(price_data: pd.DataFrame, metadata: dict | None = None) -> dict:
    expected_returns = compute_expected_returns(price_data)
    cov_matrix = compute_covariance_matrix(price_data)
    tickers = list(price_data.columns)

    state = {
        "price_data": price_data,
        "expected_returns": expected_returns,
        "cov_matrix": cov_matrix,
        "tickers": tickers,
    }

    if metadata is not None:
        state["data_metadata"] = metadata

    return state


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
        price_data, metadata = _download_and_prepare_price_data()
        market_state = _build_market_state(price_data, metadata=metadata)

        _store_cache(
            price_data=market_state["price_data"],
            expected_returns=market_state["expected_returns"],
            cov_matrix=market_state["cov_matrix"],
            tickers=market_state["tickers"],
        )

        response = {
            "price_data": _cached_price_data,
            "expected_returns": _cached_expected_returns,
            "cov_matrix": _cached_cov_matrix,
            "tickers": _cached_tickers,
            "cache_timestamp": _cache_timestamp,
            "cache_status": "fresh",
        }

        if metadata["final_missing_tickers"] or metadata["dropped_after_cleaning"]:
            response["warning"] = (
                "Some tickers were unavailable or removed during cleaning. "
                f"Missing after recovery: {metadata['final_missing_tickers']}. "
                f"Dropped after cleaning: {metadata['dropped_after_cleaning']}."
            )

        response["data_metadata"] = metadata
        return response

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