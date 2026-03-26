from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_engine import data_loader
from portfolio_engine.data_loader import load_market_state
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


app = FastAPI(title="RM Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PortfolioRequest(BaseModel):
    target_return: float
    max_volatility: Optional[float] = None


@app.get("/")
def root():
    return {"message": "RM Agent API is running"}


@app.get("/cache-status")
def cache_status():
    return data_loader.get_cache_status()


@app.post("/refresh-data")
def refresh_data():
    refreshed = data_loader.force_refresh()
    return {
        "message": "Data refreshed",
        "rows": len(refreshed["price_data"]),
        "columns": len(refreshed["price_data"].columns),
        "cache_timestamp": str(refreshed["cache_timestamp"]),
        "tickers": refreshed.get("tickers", []),
    }


@app.post("/portfolio")
def generate_portfolio(request: PortfolioRequest):
    try:
        state = load_market_state()

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

        max_return = compute_max_feasible_return(mu=expected_returns)

        weights = optimize_portfolio(
            target_return=target_return,
            price_data=price_data,
            max_volatility=max_volatility,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
        )

        weights = {k: float(v) for k, v in dict(weights).items()}

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

        concentration = float(compute_concentration(weights))

        diversification_ratio = float(
            compute_diversification_ratio(weights, cov_matrix)
        )

        sim_returns = simulate_portfolio_annual_returns(
            weights=weights,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
        )

        sim_summary = summarize_simulation_results(sim_returns)
        sim_chart = prepare_simulation_chart_data(sim_returns)

        recompute = get_recompute_schedule(portfolio_volatility)

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

        weights_percent = {k: v * 100 for k, v in weights.items()}

        meaningful_positions = [k for k, v in weights.items() if v > 0.001]
        active_positions = len(meaningful_positions)
        largest_weight = max(weights.values()) if weights else 0.0

        risk_effects = risk_contributions

        chart_data = [
            {"ticker": k, "weight": float(v)}
            for k, v in weights.items()
            if v > 0.001
        ]

        simulation_full = {
            "mean": sim_summary["mean_return"],
            "median": sim_summary["median_return"],
            "loss_probability": sim_summary["loss_probability"],
            "p5": sim_summary["percentile_5"],
            "p95": sim_summary["percentile_95"],
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
            "chart_data": chart_data,
            "risk_effects": risk_effects,
            "risk_contributions": risk_contributions,
            "concentration": concentration,
            "diversification_ratio": diversification_ratio,
            "active_positions": active_positions,
            "meaningful_positions": meaningful_positions,
            "largest_weight": largest_weight,
            "recompute_interval": recompute,
            "recompute_schedule": recompute,
            "simulation": simulation_full,
            "simulation_summary": sim_summary,
            "simulation_chart": sim_chart,
            "explanation": explanation,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}",
        )