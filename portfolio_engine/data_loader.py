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

CACHE_TTL_SECONDS = 10800  # 3 hours
DOWNLOAD_RETRIES = 3
RETRY_SLEEP_SECONDS = 5
MIN_VALID_COLUMN_RATIO = 0.8
MIN_REQUIRED_ASSETS = 2
MIN_REFRESH_SURVIVING_ASSETS = 225

CACHE_DIR = Path(os.getenv("MARKET_CACHE_DIR", "./data/market_cache"))
PRICES_PATH = CACHE_DIR / "prices.parquet"
EXPECTED_RETURNS_PATH = CACHE_DIR / "expected_returns.parquet"
COVARIANCE_PATH = CACHE_DIR / "covariance.parquet"
METADATA_PATH = CACHE_DIR / "metadata.json"
WEAK_TICKER_STATS_PATH = CACHE_DIR / "weak_ticker_stats.json"

AUTO_PRUNE_CONSECUTIVE_FAILURES = 3
AUTO_PRUNE_TOTAL_FAILURES = 4
AUTO_PRUNE_MIN_OBSERVATIONS = 6

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


def _load_weak_ticker_stats() -> dict:
    if not WEAK_TICKER_STATS_PATH.exists():
        return {}

    try:
        with open(WEAK_TICKER_STATS_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _save_weak_ticker_stats(stats: dict) -> None:
    _ensure_cache_dir()
    _write_json_atomic(WEAK_TICKER_STATS_PATH, stats)


def _get_effective_requested_tickers(
    requested_tickers: List[str],
) -> tuple[List[str], List[str], dict]:
    stats = _load_weak_ticker_stats()

    auto_pruned = []
    effective = []

    for ticker in requested_tickers:
        ticker_stats = stats.get(ticker, {})
        if ticker_stats.get("auto_pruned", False):
            auto_pruned.append(ticker)
        else:
            effective.append(ticker)

    return effective, auto_pruned, stats


def _should_auto_prune_ticker(ticker_stats: dict) -> bool:
    consecutive_failures = int(ticker_stats.get("consecutive_failures", 0))
    total_failures = int(ticker_stats.get("total_failures", 0))
    total_observations = int(ticker_stats.get("total_observations", 0))

    if consecutive_failures >= AUTO_PRUNE_CONSECUTIVE_FAILURES:
        return True

    if (
        total_observations >= AUTO_PRUNE_MIN_OBSERVATIONS
        and total_failures >= AUTO_PRUNE_TOTAL_FAILURES
    ):
        return True

    return False


def _update_weak_ticker_stats(
    requested_tickers: List[str],
    final_tickers: List[str],
    final_missing_tickers: List[str],
    dropped_after_cleaning: List[str],
    auto_pruned_tickers: List[str],
) -> dict:
    stats = _load_weak_ticker_stats()
    final_ticker_set = set(final_tickers)
    final_missing_set = set(final_missing_tickers)
    dropped_set = set(dropped_after_cleaning)

    newly_auto_pruned = []

    for ticker in requested_tickers:
        ticker_stats = stats.get(
            ticker,
            {
                "total_observations": 0,
                "total_failures": 0,
                "consecutive_failures": 0,
                "survived_runs": 0,
                "missing_runs": 0,
                "dropped_runs": 0,
                "auto_pruned": False,
                "last_status": None,
                "last_failure_reason": None,
            },
        )

        if ticker in auto_pruned_tickers:
            ticker_stats["last_status"] = "auto_pruned"
            stats[ticker] = ticker_stats
            continue

        ticker_stats["total_observations"] += 1

        if ticker in final_missing_set:
            ticker_stats["total_failures"] += 1
            ticker_stats["consecutive_failures"] += 1
            ticker_stats["missing_runs"] += 1
            ticker_stats["last_status"] = "missing"
            ticker_stats["last_failure_reason"] = "missing_after_recovery"

        elif ticker in dropped_set:
            ticker_stats["total_failures"] += 1
            ticker_stats["consecutive_failures"] += 1
            ticker_stats["dropped_runs"] += 1
            ticker_stats["last_status"] = "dropped"
            ticker_stats["last_failure_reason"] = "dropped_after_cleaning"

        elif ticker in final_ticker_set:
            ticker_stats["survived_runs"] += 1
            ticker_stats["consecutive_failures"] = 0
            ticker_stats["last_status"] = "survived"
            ticker_stats["last_failure_reason"] = None

        if (
            not ticker_stats.get("auto_pruned", False)
            and _should_auto_prune_ticker(ticker_stats)
        ):
            ticker_stats["auto_pruned"] = True
            newly_auto_pruned.append(ticker)

        stats[ticker] = ticker_stats

    _save_weak_ticker_stats(stats)

    return {
        "stats": stats,
        "newly_auto_pruned_tickers": newly_auto_pruned,
        "currently_auto_pruned_tickers": [
            ticker
            for ticker, ticker_stats in stats.items()
            if ticker_stats.get("auto_pruned", False)
        ],
    }


def _now() -> datetime.datetime:
    return datetime.datetime.now()


def _seconds_since(timestamp: datetime.datetime | None) -> float | None:
    if timestamp is None:
        return None
    return round((_now() - timestamp).total_seconds(), 3)


def _round_seconds(value: float) -> float:
    return round(float(value), 3)


def _build_metadata_summary(metadata: dict | None) -> str | None:
    if not metadata:
        return None

    configured_count = metadata.get("configured_count")
    auto_pruned_count = metadata.get("auto_pruned_count", 0)
    requested_count = metadata.get("requested_count")
    surviving_count = metadata.get("surviving_count")
    recovered_count = metadata.get("recovered_count")
    final_missing_count = metadata.get("final_missing_count")
    dropped_count = metadata.get("dropped_count")

    if requested_count is None or surviving_count is None:
        return None

    prefix = ""
    if configured_count is not None:
        prefix = (
            f"{configured_count} configured, "
            f"{auto_pruned_count} auto-pruned, "
        )

    return (
        f"{prefix}"
        f"{requested_count} requested, "
        f"{surviving_count} survived, "
        f"{recovered_count or 0} recovered, "
        f"{final_missing_count or 0} still missing, "
        f"{dropped_count or 0} dropped after cleaning"
    )


def _validate_market_state_for_cache(
    price_data: pd.DataFrame,
    expected_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    tickers: List[str],
) -> tuple[bool, str | None]:
    if price_data is None or price_data.empty:
        return False, "Refreshed price data is empty."

    if len(tickers) < MIN_REFRESH_SURVIVING_ASSETS:
        return (
            False,
            f"Refreshed universe too small for cache overwrite. "
            f"Need at least {MIN_REFRESH_SURVIVING_ASSETS} surviving assets, got {len(tickers)}.",
        )

    if expected_returns is None or len(expected_returns) != len(tickers):
        return (
            False,
            f"Expected returns length mismatch. "
            f"Expected {len(tickers)}, got {0 if expected_returns is None else len(expected_returns)}.",
        )

    if cov_matrix is None or cov_matrix.empty:
        return False, "Covariance matrix is empty."

    if cov_matrix.shape != (len(tickers), len(tickers)):
        return (
            False,
            f"Covariance matrix shape mismatch. "
            f"Expected {(len(tickers), len(tickers))}, got {cov_matrix.shape}.",
        )

    if list(expected_returns.index) != tickers:
        return False, "Expected returns index does not align with ticker order."

    if list(cov_matrix.index) != tickers or list(cov_matrix.columns) != tickers:
        return False, "Covariance matrix indices/columns do not align with ticker order."

    return True, None


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
        "data_summary": _build_metadata_summary(data_metadata),
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

        data_metadata = metadata.get("data_metadata", {})
        if isinstance(data_metadata, dict) and cache_timestamp is not None:
            data_metadata.setdefault("cache_age_seconds", _seconds_since(cache_timestamp))
            data_metadata.setdefault("summary", metadata.get("data_summary"))

        return {
            "price_data": price_data,
            "expected_returns": expected_returns,
            "cov_matrix": cov_matrix,
            "tickers": tickers,
            "cache_timestamp": cache_timestamp,
            "cache_status": metadata.get("cache_status", "disk_loaded"),
            "warning": metadata.get("warning"),
            "data_metadata": data_metadata,
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

    age = (_now() - _cache_timestamp).total_seconds()
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


def _download_missing_tickers_individually(
    missing_tickers: List[str],
) -> Tuple[pd.DataFrame, dict]:
    recovered_frames = []
    failed_recoveries = []
    per_ticker_seconds = {}

    for ticker in missing_tickers:
        ticker_start = time.perf_counter()

        try:
            single_df = _download_price_frame([ticker])
            if ticker in single_df.columns:
                recovered_frames.append(single_df[[ticker]])
            else:
                failed_recoveries.append(ticker)
        except Exception:
            failed_recoveries.append(ticker)
        finally:
            per_ticker_seconds[ticker] = _round_seconds(time.perf_counter() - ticker_start)

    if not recovered_frames:
        return pd.DataFrame(), {
            "failed_recoveries": failed_recoveries,
            "individual_recovery_seconds_by_ticker": per_ticker_seconds,
        }

    combined = pd.concat(recovered_frames, axis=1)
    combined = combined.loc[:, ~combined.columns.duplicated()]
    combined = combined.sort_index()

    return combined, {
        "failed_recoveries": failed_recoveries,
        "individual_recovery_seconds_by_ticker": per_ticker_seconds,
    }


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
    configured_tickers = list(TICKERS)
    requested_tickers, auto_pruned_tickers, weak_ticker_stats = _get_effective_requested_tickers(
        configured_tickers
    )

    if not requested_tickers:
        raise ValueError(
            "All configured tickers are currently auto-pruned. "
            "Review weak ticker stats before refreshing again."
        )

    refresh_start = time.perf_counter()

    batch_download_start = time.perf_counter()
    initial_price_data = _download_price_frame(requested_tickers)
    batch_download_seconds = _round_seconds(time.perf_counter() - batch_download_start)

    missing_after_batch = _find_missing_tickers(initial_price_data, requested_tickers)

    recovered_data = pd.DataFrame()
    recovery_details = {
        "failed_recoveries": [],
        "individual_recovery_seconds_by_ticker": {},
    }
    individual_recovery_seconds = 0.0

    if missing_after_batch:
        recovery_start = time.perf_counter()
        recovered_data, recovery_details = _download_missing_tickers_individually(
            missing_after_batch
        )
        individual_recovery_seconds = _round_seconds(time.perf_counter() - recovery_start)

    combine_start = time.perf_counter()
    combined_price_data = _combine_price_frames(initial_price_data, recovered_data)
    combine_seconds = _round_seconds(time.perf_counter() - combine_start)

    still_missing = _find_missing_tickers(combined_price_data, requested_tickers)

    cleaning_start = time.perf_counter()
    cleaned_price_data, dropped_after_cleaning = _clean_price_data(combined_price_data)
    cleaning_seconds = _round_seconds(time.perf_counter() - cleaning_start)

    recovered_tickers = [
        ticker for ticker in missing_after_batch if ticker in recovered_data.columns
    ]

    weak_ticker_result = _update_weak_ticker_stats(
        requested_tickers=requested_tickers,
        final_tickers=list(cleaned_price_data.columns),
        final_missing_tickers=still_missing,
        dropped_after_cleaning=dropped_after_cleaning,
        auto_pruned_tickers=auto_pruned_tickers,
    )

    metadata = {
        "configured_tickers": configured_tickers,
        "configured_count": len(configured_tickers),
        "auto_pruned_tickers": auto_pruned_tickers,
        "auto_pruned_count": len(auto_pruned_tickers),
        "requested_tickers": requested_tickers,
        "requested_count": len(requested_tickers),
        "initial_missing_tickers": missing_after_batch,
        "initial_missing_count": len(missing_after_batch),
        "recovered_tickers": recovered_tickers,
        "recovered_count": len(recovered_tickers),
        "failed_recoveries": recovery_details.get("failed_recoveries", []),
        "final_missing_tickers": still_missing,
        "final_missing_count": len(still_missing),
        "dropped_after_cleaning": dropped_after_cleaning,
        "dropped_count": len(dropped_after_cleaning),
        "final_tickers": list(cleaned_price_data.columns),
        "surviving_count": int(cleaned_price_data.shape[1]),
        "price_rows": int(cleaned_price_data.shape[0]),
        "price_columns": int(cleaned_price_data.shape[1]),
        "newly_auto_pruned_tickers": weak_ticker_result["newly_auto_pruned_tickers"],
        "currently_auto_pruned_tickers": weak_ticker_result["currently_auto_pruned_tickers"],
        "timings": {
            "batch_download_seconds": batch_download_seconds,
            "individual_recovery_seconds": individual_recovery_seconds,
            "combine_seconds": combine_seconds,
            "cleaning_seconds": cleaning_seconds,
            "individual_recovery_seconds_by_ticker": recovery_details.get(
                "individual_recovery_seconds_by_ticker", {}
            ),
            "download_and_prepare_total_seconds": _round_seconds(
                time.perf_counter() - refresh_start
            ),
        },
    }

    metadata["summary"] = _build_metadata_summary(metadata)

    return cleaned_price_data, metadata


def _build_market_state(price_data: pd.DataFrame, metadata: dict | None = None) -> dict:
    expected_returns_start = time.perf_counter()
    expected_returns = compute_expected_returns(price_data)
    expected_returns_seconds = _round_seconds(time.perf_counter() - expected_returns_start)

    covariance_start = time.perf_counter()
    cov_matrix = compute_covariance_matrix(price_data)
    covariance_seconds = _round_seconds(time.perf_counter() - covariance_start)

    tickers = list(price_data.columns)

    if metadata is not None:
        metadata.setdefault("timings", {})
        metadata["timings"]["expected_returns_seconds"] = expected_returns_seconds
        metadata["timings"]["covariance_seconds"] = covariance_seconds

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
    _cache_timestamp = _now()

    if isinstance(data_metadata, dict):
        data_metadata = dict(data_metadata)
        data_metadata["cache_age_seconds"] = 0.0
        data_metadata["summary"] = _build_metadata_summary(data_metadata)

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
        metadata = dict(_cached_data_metadata or {})
        metadata["cache_age_seconds"] = _seconds_since(_cache_timestamp)
        metadata["summary"] = metadata.get("summary") or _build_metadata_summary(metadata)

        return {
            "price_data": _cached_price_data,
            "expected_returns": _cached_expected_returns,
            "cov_matrix": _cached_cov_matrix,
            "tickers": _cached_tickers,
            "cache_timestamp": _cache_timestamp,
            "cache_status": "fresh",
            "data_metadata": metadata,
        }

    refresh_total_start = time.perf_counter()

    try:
        price_data, metadata = _download_and_prepare_price_data()
        market_state = _build_market_state(price_data, metadata=metadata)

        is_healthy, validation_error = _validate_market_state_for_cache(
            price_data=market_state["price_data"],
            expected_returns=market_state["expected_returns"],
            cov_matrix=market_state["cov_matrix"],
            tickers=market_state["tickers"],
        )

        metadata.setdefault("validation", {})
        metadata["validation"]["cache_overwrite_allowed"] = is_healthy
        metadata["validation"]["cache_overwrite_error"] = validation_error

        metadata.setdefault("timings", {})
        metadata["timings"]["total_refresh_seconds"] = _round_seconds(
            time.perf_counter() - refresh_total_start
        )

        if not is_healthy:
            if has_any_cache:
                fallback_metadata = dict(_cached_data_metadata or {})
                fallback_metadata["cache_age_seconds"] = _seconds_since(_cache_timestamp)
                fallback_metadata["summary"] = (
                    fallback_metadata.get("summary")
                    or _build_metadata_summary(fallback_metadata)
                )

                return {
                    "price_data": _cached_price_data,
                    "expected_returns": _cached_expected_returns,
                    "cov_matrix": _cached_cov_matrix,
                    "tickers": _cached_tickers,
                    "cache_timestamp": _cache_timestamp,
                    "cache_status": "stale_fallback",
                    "warning": (
                        "Refreshed market data failed validation, so existing cache was kept. "
                        f"Reason: {validation_error}"
                    ),
                    "data_metadata": fallback_metadata,
                    "refresh_validation": metadata.get("validation"),
                }

            raise ValueError(
                f"Refreshed market data failed validation and no existing cache is available. "
                f"Reason: {validation_error}"
            )

        _store_cache(
            price_data=market_state["price_data"],
            expected_returns=market_state["expected_returns"],
            cov_matrix=market_state["cov_matrix"],
            tickers=market_state["tickers"],
            data_metadata=metadata,
        )

        response_metadata = dict(_cached_data_metadata or {})
        response_metadata["cache_age_seconds"] = _seconds_since(_cache_timestamp)
        response_metadata["summary"] = (
            response_metadata.get("summary")
            or _build_metadata_summary(response_metadata)
        )

        response = {
            "price_data": _cached_price_data,
            "expected_returns": _cached_expected_returns,
            "cov_matrix": _cached_cov_matrix,
            "tickers": _cached_tickers,
            "cache_timestamp": _cache_timestamp,
            "cache_status": "fresh",
            "data_metadata": response_metadata,
            "refresh_validation": metadata.get("validation"),
        }

        if response_metadata.get("final_missing_tickers") or response_metadata.get(
            "dropped_after_cleaning"
        ):
            response["warning"] = (
                "Some tickers were unavailable or removed during cleaning. "
                f"Missing after recovery: {response_metadata.get('final_missing_tickers', [])}. "
                f"Dropped after cleaning: {response_metadata.get('dropped_after_cleaning', [])}."
            )

        if response_metadata.get("newly_auto_pruned_tickers"):
            auto_pruned_warning = (
                f" Newly auto-pruned tickers: {response_metadata.get('newly_auto_pruned_tickers', [])}."
            )
            response["warning"] = (response.get("warning") or "") + auto_pruned_warning
            response["warning"] = response["warning"].strip()

        return response

    except Exception as e:
        if has_any_cache:
            metadata = dict(_cached_data_metadata or {})
            metadata["cache_age_seconds"] = _seconds_since(_cache_timestamp)
            metadata["summary"] = metadata.get("summary") or _build_metadata_summary(metadata)

            return {
                "price_data": _cached_price_data,
                "expected_returns": _cached_expected_returns,
                "cov_matrix": _cached_cov_matrix,
                "tickers": _cached_tickers,
                "cache_timestamp": _cache_timestamp,
                "cache_status": "stale_fallback",
                "warning": f"Using stale cached market data because refresh failed: {e}",
                "data_metadata": metadata,
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

    metadata = dict(_cached_data_metadata or {})
    metadata["cache_age_seconds"] = _seconds_since(_cache_timestamp)
    metadata["summary"] = metadata.get("summary") or _build_metadata_summary(metadata)

    return {
        "price_data": _cached_price_data,
        "expected_returns": _cached_expected_returns,
        "cov_matrix": _cached_cov_matrix,
        "tickers": _cached_tickers,
        "cache_timestamp": _cache_timestamp,
        "cache_status": "fresh" if is_valid else "stale_cached",
        "data_metadata": metadata,
        "warning": None if is_valid else "Using stale cached market data.",
    }


def get_cache_status() -> dict:
    _hydrate_memory_cache_from_disk_if_needed()

    metadata = dict(_cached_data_metadata or {})
    metadata["cache_age_seconds"] = _seconds_since(_cache_timestamp)
    metadata["summary"] = metadata.get("summary") or _build_metadata_summary(metadata)

    return {
        "cache_valid": _is_cache_valid(),
        "cache_timestamp": _cache_timestamp.isoformat() if _cache_timestamp else None,
        "cache_age_seconds": _seconds_since(_cache_timestamp),
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "num_assets": len(_cached_tickers) if _cached_tickers is not None else 0,
        "tickers": _cached_tickers if _cached_tickers is not None else [],
        "cache_dir": str(CACHE_DIR),
        "disk_cache_present": _has_disk_cache(),
        "data_summary": metadata.get("summary"),
        "data_metadata": metadata,
    }


def get_weak_ticker_status() -> dict:
    stats = _load_weak_ticker_stats()

    auto_pruned = {
        ticker: ticker_stats
        for ticker, ticker_stats in stats.items()
        if ticker_stats.get("auto_pruned", False)
    }

    weak_candidates = {
        ticker: ticker_stats
        for ticker, ticker_stats in stats.items()
        if (
            not ticker_stats.get("auto_pruned", False)
            and (
                ticker_stats.get("consecutive_failures", 0) > 0
                or ticker_stats.get("total_failures", 0) > 0
            )
        )
    }

    return {
        "auto_pruned_count": len(auto_pruned),
        "auto_pruned_tickers": auto_pruned,
        "weak_candidate_count": len(weak_candidates),
        "weak_candidates": weak_candidates,
    }


def force_refresh() -> dict:
    return refresh_market_cache(force_refresh=True)