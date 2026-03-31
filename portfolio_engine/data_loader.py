import datetime
import json
import os
import time
from pathlib import Path
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
_cached_data_metadata = None

CACHE_TTL_SECONDS = 10800  # 6 hours
DOWNLOAD_RETRIES = 3
RETRY_SLEEP_SECONDS = 5
MIN_VALID_COLUMN_RATIO = 0.8
MIN_REQUIRED_ASSETS = 2

CACHE_DIR = Path(os.getenv("MARKET_CACHE_DIR", "./data/market_cache"))
PRICES_PATH = CACHE_DIR / "prices.parquet"
EXPECTED_RETURNS_PATH = CACHE_DIR / "expected_returns.parquet"
COVARIANCE_PATH = CACHE_DIR / "covariance.parquet"
METADATA_PATH = CACHE_DIR / "metadata.json"

print("MARKET_CACHE_DIR env:", os.getenv("MARKET_CACHE_DIR"))
print("Resolved CACHE_DIR:", CACHE_DIR)


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _has_disk_cache() -> bool:
    return (
        PRICES_PATH.exists()
        and EXPECTED_RETURNS_PATH.exists()
        and COVARIANCE_PATH.exists()
        and METADATA_PATH.exists()
    )


def _write_json_atomic(path: Path, payload: dict) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def _write_parquet_atomic(df: pd.DataFrame, path: Path) -> None:
    temp_path = path.with_suffix(path.suffix + ".tmp")
    df.to_parquet(temp_path)
    temp_path.replace(path)


def _save_cache_to_disk(
    price_data: pd.DataFrame,
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    tickers: List[str],
    cache_timestamp: datetime.datetime,
    data_metadata: dict | None = None,
    warning: str | None = None,
    cache_status: str = "fresh",
) -> None:
    _ensure_cache_dir()

    expected_returns_df = expected_returns.to_frame(name="expected_return")

    metadata = {
        "cache_timestamp": cache_timestamp.isoformat(),
        "tickers": tickers,
        "num_assets": len(tickers),
        "rows": int(price_data.shape[0]),
        "columns": int(price_data.shape[1]),
        "cache_status": cache_status,
        "warning": warning,
        "start_date": str(START_DATE),
        "data_metadata": data_metadata or {},
    }

    _write_parquet_atomic(price_data, PRICES_PATH)
    _write_parquet_atomic(expected_returns_df, EXPECTED_RETURNS_PATH)
    _write_parquet_atomic(cov_matrix, COVARIANCE_PATH)
    _write_json_atomic(METADATA_PATH, metadata)


def _load_cache_from_disk() -> dict | None:
    if not _has_disk_cache():
        return None

    try:
        price_data = pd.read_parquet(PRICES_PATH)
        expected_returns_df = pd.read_parquet(EXPECTED_RETURNS_PATH)
        cov_matrix = pd.read_parquet(COVARIANCE_PATH)

        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        expected_returns = expected_returns_df["expected_return"]
        tickers = metadata.get("tickers", list(price_data.columns))
        cache_timestamp_raw = metadata.get("cache_timestamp")
        cache_timestamp = (
            datetime.datetime.fromisoformat(cache_timestamp_raw)
            if cache_timestamp_raw
            else None
        )

        return {
            "price_data": price_data,
            "expected_returns": expected_returns,
            "cov_matrix": cov_matrix,
            "tickers": tickers,
            "cache_timestamp": cache_timestamp,
            "cache_status": metadata.get("cache_status", "disk_loaded"),
            "warning": metadata.get("warning"),
            "data_metadata": metadata.get("data_metadata", {}),
        }

    except Exception:
        return None


def _hydrate_memory_cache_from_disk_if_needed() -> bool:
    global _cached_price_data
    global _cached_expected_returns
    global _cached_cov_matrix
    global _cached_tickers
    global _cache_timestamp
    global _cached_data_metadata

    has_any_cache = (
        _cached_price_data is not None
        and _cached_expected_returns is not None
        and _cached_cov_matrix is not None
        and _cached_tickers is not None
        and _cache_timestamp is not None
    )

    if has_any_cache:
        return True

    disk_cache = _load_cache_from_disk()
    if disk_cache is None:
        return False

    _cached_price_data = disk_cache["price_data"]
    _cached_expected_returns = disk_cache["expected_returns"]
    _cached_cov_matrix = disk_cache["cov_matrix"]
    _cached_tickers = disk_cache["tickers"]
    _cache_timestamp = disk_cache["cache_timestamp"]
    _cached_data_metadata = disk_cache.get("data_metadata")

    return True


def _is_cache_valid() -> bool:
    global _cache_timestamp

    if _cache_timestamp is None:
        return False

    age = (datetime.datetime.now() - _cache_timestamp).total_seconds()
    return age < CACHE_TTL_SECONDS


def _normalize_to_dataframe(data: pd.DataFrame, requested_tickers: List[str]) -> pd.DataFrame:
    if data is None or data.empty:
        raise ValueError("Yahoo Finance returned no data.")

    if isinstance(data, pd.Series):
        ticker_name = requested_tickers[0] if requested_tickers else "UNKNOWN"
        data = data.to_frame(name=ticker_name)

    if not isinstance(data, pd.DataFrame):
        raise ValueError("Yahoo Finance returned an unexpected data format.")

    return data


def _extract_price_frame(raw: pd.DataFrame, requested_tickers: List[str]) -> pd.DataFrame:
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
    recovered_frames = []

    for ticker in missing_tickers:
        try:
            single_df = _download_price_frame([ticker])
            if ticker in single_df.columns:
                recovered_frames.append(single_df[[ticker]])
        except Exception:
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


def _store_cache(
    price_data: pd.DataFrame,
    expected_returns,
    cov_matrix,
    tickers,
    data_metadata: dict | None = None,
) -> None:
    global _cached_price_data
    global _cached_expected_returns
    global _cached_cov_matrix
    global _cached_tickers
    global _cache_timestamp
    global _cached_data_metadata

    _cached_price_data = price_data
    _cached_expected_returns = expected_returns
    _cached_cov_matrix = cov_matrix
    _cached_tickers = tickers
    _cache_timestamp = datetime.datetime.now()
    _cached_data_metadata = data_metadata

    _save_cache_to_disk(
        price_data=price_data,
        expected_returns=expected_returns,
        cov_matrix=cov_matrix,
        tickers=tickers,
        cache_timestamp=_cache_timestamp,
        data_metadata=data_metadata,
        warning=None,
        cache_status="fresh",
    )


def refresh_market_cache(force_refresh: bool = False) -> dict:
    global _cached_price_data
    global _cached_expected_returns
    global _cached_cov_matrix
    global _cached_tickers
    global _cache_timestamp
    global _cached_data_metadata

    _hydrate_memory_cache_from_disk_if_needed()

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
            "data_metadata": _cached_data_metadata,
        }

    try:
        price_data, metadata = _download_and_prepare_price_data()
        market_state = _build_market_state(price_data, metadata=metadata)

        _store_cache(
            price_data=market_state["price_data"],
            expected_returns=market_state["expected_returns"],
            cov_matrix=market_state["cov_matrix"],
            tickers=market_state["tickers"],
            data_metadata=metadata,
        )

        response = {
            "price_data": _cached_price_data,
            "expected_returns": _cached_expected_returns,
            "cov_matrix": _cached_cov_matrix,
            "tickers": _cached_tickers,
            "cache_timestamp": _cache_timestamp,
            "cache_status": "fresh",
            "data_metadata": metadata,
        }

        if metadata["final_missing_tickers"] or metadata["dropped_after_cleaning"]:
            response["warning"] = (
                "Some tickers were unavailable or removed during cleaning. "
                f"Missing after recovery: {metadata['final_missing_tickers']}. "
                f"Dropped after cleaning: {metadata['dropped_after_cleaning']}."
            )

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
                "data_metadata": _cached_data_metadata,
            }

        raise ValueError(
            f"Unable to load market data and no cached data is available. Original error: {e}"
        )


def load_price_data(force_refresh: bool = False) -> pd.DataFrame:
    return refresh_market_cache(force_refresh=force_refresh)["price_data"]


def load_market_state(force_refresh: bool = False) -> dict:
    return refresh_market_cache(force_refresh=force_refresh)


def load_cached_market_state(require_valid: bool = True) -> dict:
    """
    Loads market state from memory/disk cache only.
    Never triggers a Yahoo refresh.

    If require_valid=True, stale cache is rejected.
    If require_valid=False, stale cache is allowed.
    """
    global _cached_price_data
    global _cached_expected_returns
    global _cached_cov_matrix
    global _cached_tickers
    global _cache_timestamp
    global _cached_data_metadata

    _hydrate_memory_cache_from_disk_if_needed()

    has_any_cache = (
        _cached_price_data is not None
        and _cached_expected_returns is not None
        and _cached_cov_matrix is not None
        and _cached_tickers is not None
        and _cache_timestamp is not None
    )

    if not has_any_cache:
        raise ValueError(
            "No cached market data is available. Please run /refresh-data first."
        )

    is_valid = _is_cache_valid()
    if require_valid and not is_valid:
        raise ValueError(
            "Cached market data is stale. Please run /refresh-data before generating a portfolio."
        )

    return {
        "price_data": _cached_price_data,
        "expected_returns": _cached_expected_returns,
        "cov_matrix": _cached_cov_matrix,
        "tickers": _cached_tickers,
        "cache_timestamp": _cache_timestamp,
        "cache_status": "fresh" if is_valid else "stale_cached",
        "data_metadata": _cached_data_metadata,
        "warning": None if is_valid else "Using stale cached market data.",
    }


def get_cache_status() -> dict:
    _hydrate_memory_cache_from_disk_if_needed()

    return {
        "cache_valid": _is_cache_valid(),
        "cache_timestamp": _cache_timestamp.isoformat() if _cache_timestamp else None,
        "num_assets": len(_cached_tickers) if _cached_tickers is not None else 0,
        "tickers": _cached_tickers if _cached_tickers is not None else [],
        "cache_dir": str(CACHE_DIR),
        "disk_cache_present": _has_disk_cache(),
    }


def force_refresh() -> dict:
    return refresh_market_cache(force_refresh=True)