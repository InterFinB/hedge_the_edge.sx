from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from collections import defaultdict
import time
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_engine.config import (
    TICKER_TO_NAME,
    TICKER_TO_CATEGORY,
)

from portfolio_engine import data_loader
from portfolio_engine.data_loader import load_cached_market_state
from portfolio_engine.optimizer import (
    optimize_portfolio,
    compute_max_feasible_return,
)
from portfolio_engine.risk import (
    compute_portfolio_volatility,
    compute_portfolio_return,
)
from portfolio_engine.diagnostics import (
    compute_risk_contributions,
    compute_concentration,
    compute_diversification_ratio,
)
from portfolio_engine.simulation import (
    simulate_portfolio_annual_returns,
    summarize_simulation_results,
    prepare_simulation_chart_data,
)
from portfolio_engine.recompute_schedule import get_recompute_schedule
from explanation_layer import generate_explanation

from ai.context.builder import build_ai_context
from ai.schemas import AskPortfolioRequest

try:
    from ai.services.ask_portfolio_service import ask_portfolio_question
    ASK_PORTFOLIO_SERVICE_AVAILABLE = True
except Exception:
    ask_portfolio_question = None
    ASK_PORTFOLIO_SERVICE_AVAILABLE = False


app = FastAPI(title="RM Agent API")

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
allowed_origins = [
    origin.strip()
    for origin in frontend_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PortfolioRequest(BaseModel):
    target_return: float
    max_volatility: Optional[float] = None


def _serialize_market_state(state: dict) -> dict:
    tickers = state.get("tickers", [])
    cache_timestamp = state.get("cache_timestamp")

    return {
        "cache_status": state.get("cache_status", "unknown"),
        "cache_timestamp": (
            cache_timestamp.isoformat() if cache_timestamp is not None else None
        ),
        "warning": state.get("warning"),
        "data_metadata": state.get("data_metadata"),
        "num_assets": len(tickers),
        "tickers": tickers,
    }


def _serialize_refresh_result(refreshed: dict) -> dict:
    price_data = refreshed["price_data"]
    metadata = refreshed.get("data_metadata") or {}

    return {
        "message": "Data refresh completed",
        "rows": len(price_data),
        "columns": len(price_data.columns),
        "summary": metadata.get("summary"),
        "market_data": _serialize_market_state(refreshed),
        "refresh_validation": refreshed.get("refresh_validation"),
    }


def _build_category_exposure(weights: dict[str, float]) -> list[dict]:
    exposure = defaultdict(float)

    for ticker, weight in weights.items():
      category = TICKER_TO_CATEGORY.get(ticker, "Uncategorized")
      exposure[category] += float(weight)

    result = [
        {
            "category": category,
            "weight": round(weight, 8),
            "weight_percent": round(weight * 100, 4),
        }
        for category, weight in exposure.items()
    ]

    result.sort(key=lambda x: x["weight"], reverse=True)
    return result


def _build_top_positions(weights: dict[str, float], limit: int = 5) -> list[dict]:
    top = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [
        {
            "ticker": ticker,
            "name": TICKER_TO_NAME.get(ticker, ticker),
            "category": TICKER_TO_CATEGORY.get(ticker, "Uncategorized"),
            "weight": round(float(weight), 8),
            "weight_percent": round(float(weight) * 100, 4),
        }
        for ticker, weight in top
    ]


def _build_universe_status(state: dict) -> dict:
    metadata = state.get("data_metadata") or {}

    configured_count = metadata.get("configured_count")
    requested_count = metadata.get("requested_count")
    surviving_count = metadata.get("surviving_count")
    auto_pruned_count = metadata.get("auto_pruned_count", 0)
    dropped_after_cleaning = metadata.get("dropped_after_cleaning", [])
    final_missing_tickers = metadata.get("final_missing_tickers", [])

    effective_universe_count = surviving_count
    if effective_universe_count is None:
        effective_universe_count = len(state.get("tickers", []))

    return {
        "configured_count": configured_count,
        "requested_count": requested_count,
        "surviving_count": surviving_count,
        "effective_universe_count": effective_universe_count,
        "auto_pruned_count": auto_pruned_count,
        "auto_pruned_tickers": metadata.get("auto_pruned_tickers", []),
        "currently_auto_pruned_tickers": metadata.get(
            "currently_auto_pruned_tickers", []
        ),
        "newly_auto_pruned_tickers": metadata.get(
            "newly_auto_pruned_tickers", []
        ),
        "dropped_after_cleaning": dropped_after_cleaning,
        "final_missing_tickers": final_missing_tickers,
        "cache_status": state.get("cache_status"),
        "cache_warning": state.get("warning"),
        "refresh_summary": metadata.get("summary"),
    }


@app.get("/")
def root():
    return {
        "message": "RM Agent API is running",
        "allowed_origins": allowed_origins,
        "ask_portfolio_service_available": ASK_PORTFOLIO_SERVICE_AVAILABLE,
    }


@app.get("/cache-status")
def cache_status():
    try:
        return data_loader.get_cache_status()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read cache status: {str(e)}",
        )


@app.get("/weak-tickers")
def weak_tickers():
    try:
        return data_loader.get_weak_ticker_status()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read weak ticker status: {str(e)}",
        )


@app.post("/refresh-data")
def refresh_data():
    try:
        refreshed = data_loader.force_refresh()
        return _serialize_refresh_result(refreshed)

    except ValueError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Market data refresh failed: {str(e)}",
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error during refresh: {str(e)}",
        )


@app.post("/portfolio")
def generate_portfolio(request: PortfolioRequest):
    total_start = time.perf_counter()

    try:
        load_state_start = time.perf_counter()
        state = load_cached_market_state(require_valid=False)
        load_state_seconds = round(time.perf_counter() - load_state_start, 6)

        price_data = state["price_data"]
        expected_returns = state["expected_returns"]
        cov_matrix = state["cov_matrix"]
        tickers = state["tickers"]

        target_return = float(request.target_return)
        max_volatility = (
            float(request.max_volatility)
            if request.max_volatility is not None
            else None
        )

        max_return_start = time.perf_counter()
        max_return = compute_max_feasible_return(mu=expected_returns)
        max_return_seconds = round(time.perf_counter() - max_return_start, 6)

        optimize_start = time.perf_counter()
        weights, concentration_diagnostics = optimize_portfolio(
            target_return=target_return,
            price_data=price_data,
            max_volatility=max_volatility,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            return_diagnostics=True,
        )
        optimize_seconds = round(time.perf_counter() - optimize_start, 6)

        weights = {k: float(v) for k, v in dict(weights).items()}

        metrics_start = time.perf_counter()

        portfolio_return = float(
            compute_portfolio_return(weights, expected_returns)
        )

        portfolio_volatility = float(
            compute_portfolio_volatility(weights, cov_matrix)
        )

        risk_contributions = compute_risk_contributions(
            weights,
            cov_matrix,
        )
        risk_contributions = {
            k: float(v) for k, v in dict(risk_contributions).items()
        }

        concentration = float(compute_concentration(weights))

        diversification_ratio = float(
            compute_diversification_ratio(weights, cov_matrix)
        )

        metrics_seconds = round(time.perf_counter() - metrics_start, 6)

        simulation_start = time.perf_counter()

        sim_returns = simulate_portfolio_annual_returns(
            weights=weights,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
        )

        sim_summary = summarize_simulation_results(sim_returns)
        sim_chart = prepare_simulation_chart_data(sim_returns)

        simulation_seconds = round(time.perf_counter() - simulation_start, 6)

        structure_start = time.perf_counter()

        recompute = get_recompute_schedule(portfolio_volatility)

        weights_percent = {k: float(v) * 100 for k, v in weights.items()}

        meaningful_positions = [k for k, v in weights.items() if v > 0.001]
        active_positions = len(meaningful_positions)
        largest_weight = max(weights.values()) if weights else 0.0

        pre_prune_assets = concentration_diagnostics.get("pre_prune_assets")
        post_prune_assets = concentration_diagnostics.get("post_prune_assets")
        concentration_threshold_used = concentration_diagnostics.get(
            "concentration_threshold_used"
        )
        concentration_capped = bool(
            concentration_diagnostics.get("concentration_capped", 0)
        )

        risk_effects = risk_contributions

        chart_data = [
            {"ticker": k, "weight": float(v)}
            for k, v in weights.items()
            if v > 0.001
        ]

        category_exposure = _build_category_exposure(weights)
        universe_status = _build_universe_status(state)
        market_data = _serialize_market_state(state)

        simulation_full = {
            "mean": sim_summary["mean_return"],
            "median": sim_summary["median_return"],
            "loss_probability": sim_summary["loss_probability"],
            "p5": sim_summary["percentile_5"],
            "p95": sim_summary["percentile_95"],
        }

        explanation_input = build_ai_context(
            target_return=target_return,
            max_volatility=max_volatility,
            portfolio_return=portfolio_return,
            portfolio_volatility=portfolio_volatility,
            weights=weights,
            category_exposure=category_exposure,
            risk_contributions=risk_contributions,
            diversification_ratio=diversification_ratio,
            concentration=concentration,
            active_positions=active_positions,
            largest_weight=largest_weight,
            pre_prune_assets=pre_prune_assets,
            post_prune_assets=post_prune_assets,
            concentration_threshold_used=concentration_threshold_used,
            concentration_capped=concentration_capped,
            simulation_summary=sim_summary,
            universe_status=universe_status,
            market_data=market_data,
            explanation=None,
        )

        structure_seconds = round(time.perf_counter() - structure_start, 6)

        explanation_start = time.perf_counter()

        explanation = generate_explanation(
            desired_return=target_return,
            expected_portfolio_return=portfolio_return,
            portfolio_volatility=portfolio_volatility,
            weights=weights,
            risk_contributions=risk_contributions,
            diversification_ratio=diversification_ratio,
            concentration=concentration,
            feasible=None
            if max_volatility is None
            else bool(portfolio_volatility <= max_volatility + 1e-6),
            max_volatility=max_volatility,
            max_weight_constraint=0.35,
            simulation_mean_return=sim_summary["mean_return"],
            simulation_median_return=sim_summary["median_return"],
            simulation_loss_probability=sim_summary["loss_probability"],
            simulation_percentile_5=sim_summary["percentile_5"],
            simulation_percentile_95=sim_summary["percentile_95"],
        )

        explanation_seconds = round(time.perf_counter() - explanation_start, 6)

        ai_context = build_ai_context(
            target_return=target_return,
            max_volatility=max_volatility,
            portfolio_return=portfolio_return,
            portfolio_volatility=portfolio_volatility,
            weights=weights,
            category_exposure=category_exposure,
            risk_contributions=risk_contributions,
            diversification_ratio=diversification_ratio,
            concentration=concentration,
            active_positions=active_positions,
            largest_weight=largest_weight,
            pre_prune_assets=pre_prune_assets,
            post_prune_assets=post_prune_assets,
            concentration_threshold_used=concentration_threshold_used,
            concentration_capped=concentration_capped,
            simulation_summary=sim_summary,
            universe_status=universe_status,
            market_data=market_data,
            explanation=explanation,
        )

        total_seconds = round(time.perf_counter() - total_start, 6)

        portfolio_timing = {
            "load_cached_market_state_seconds": load_state_seconds,
            "compute_max_return_seconds": max_return_seconds,
            "optimization_seconds": optimize_seconds,
            "portfolio_metrics_seconds": metrics_seconds,
            "simulation_seconds": simulation_seconds,
            "response_structuring_seconds": structure_seconds,
            "explanation_seconds": explanation_seconds,
            "total_portfolio_request_seconds": total_seconds,
        }

        return {
            "desired_return": target_return,
            "target_return": target_return,
            "expected_portfolio_return": portfolio_return,
            "portfolio_return": portfolio_return,
            "portfolio_volatility": portfolio_volatility,
            "max_return": float(max_return),
            "weights": weights,
            "weights_percent": weights_percent,
            "tickers": tickers,
            "ticker_to_name": TICKER_TO_NAME,
            "ticker_to_category": TICKER_TO_CATEGORY,
            "chart_data": chart_data,
            "category_exposure": category_exposure,
            "risk_effects": risk_effects,
            "risk_contributions": risk_contributions,
            "concentration": concentration,
            "diversification_ratio": diversification_ratio,
            "active_positions": active_positions,
            "meaningful_positions": meaningful_positions,
            "largest_weight": largest_weight,
            "pre_prune_assets": pre_prune_assets,
            "post_prune_assets": post_prune_assets,
            "concentration_threshold_used": concentration_threshold_used,
            "concentration_capped": concentration_capped,
            "top_positions": _build_top_positions(weights, limit=5),
            "recompute_interval": recompute,
            "recompute_schedule": recompute,
            "simulation": simulation_full,
            "simulation_summary": sim_summary,
            "simulation_chart": sim_chart,
            "portfolio_timing": portfolio_timing,
            "universe_status": universe_status,
            "explanation_input": explanation_input,
            "explanation": explanation,
            "market_data": market_data,
            "ai_context": ai_context,
        }

    except ValueError as e:
        error_text = str(e).lower()

        if (
            "no cached market data is available" in error_text
            or "market data not ready" in error_text
        ):
            raise HTTPException(
                status_code=503,
                detail=str(e),
            )

        if (
            "unable to load market data" in error_text
            or "failed to download" in error_text
            or "no cached data is available" in error_text
            or "price data" in error_text
            or "yahoo finance" in error_text
        ):
            raise HTTPException(
                status_code=503,
                detail=f"Market data unavailable: {str(e)}",
            )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}",
        )


@app.post("/ask-portfolio")
def ask_portfolio(request: AskPortfolioRequest):
    if not ASK_PORTFOLIO_SERVICE_AVAILABLE or ask_portfolio_question is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "AI portfolio chat service is not available. "
                "Make sure ai/services/ask_portfolio_service.py exists in the deployed backend."
            ),
        )

    try:
        response = ask_portfolio_question(
            question=request.question,
            ai_context=request.ai_context,
            conversation=request.conversation,
        )
        return response.model_dump()

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected AI server error: {str(e)}",
        )