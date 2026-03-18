from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_engine import data_loader
from portfolio_engine.data_loader import load_price_data
from portfolio_engine.optimizer import optimize_portfolio
from portfolio_engine.risk import (
    compute_portfolio_volatility,
    compute_portfolio_return,
)
from portfolio_engine.input_parser import parse_percentage_input
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
from explanation_layer.explanation import generate_explanation_bullets

app = FastAPI(title="RM Agent API")


class PortfolioRequest(BaseModel):
    target_return: str
    max_volatility: Optional[str] = None


@app.get("/")
def home():
    return {"message": "RM Agent API is running"}


@app.get("/cache-status")
def cache_status():
    return {
        "cache_timestamp": str(data_loader._cache_timestamp),
        "cache_loaded": data_loader._cached_price_data is not None,
    }


@app.post("/refresh-data")
def refresh_data():
    price_data = load_price_data(force_refresh=True)
    return {
        "message": "Market data cache refreshed successfully.",
        "rows": len(price_data),
        "columns": len(price_data.columns),
    }


@app.post("/portfolio")
def generate_portfolio(request: PortfolioRequest):
    try:
        target_return = float(parse_percentage_input(request.target_return))

        max_volatility = None
        if (
            request.max_volatility is not None
            and request.max_volatility.strip() != ""
        ):
            max_volatility = float(
                parse_percentage_input(request.max_volatility)
            )

        price_data = load_price_data()

        weights = optimize_portfolio(
            target_return=target_return,
            price_data=price_data,
            max_volatility=max_volatility,
        )

        portfolio_volatility = float(
            compute_portfolio_volatility(weights, price_data)
        )
        portfolio_return = float(
            compute_portfolio_return(weights, price_data)
        )

        raw_weights = {k: float(v) for k, v in dict(weights).items()}

        chart_weights = {
            k: float(v)
            for k, v in raw_weights.items()
            if v > 0.001
        }

        clean_weights = {
            k: f"{round(v * 100, 2)}%"
            for k, v in chart_weights.items()
        }

        risk_contributions = compute_risk_contributions(raw_weights, price_data)
        total_absolute_risk = sum(abs(v) for v in risk_contributions.values())

        clean_risk_contributions = {}
        risk_effects = {}
        chart_risk_contributions = {}

        if total_absolute_risk != 0:
            for k, v in risk_contributions.items():
                if raw_weights.get(k, 0) <= 0.001:
                    continue

                percent = (abs(v) / total_absolute_risk) * 100

                if v < 0:
                    percent = -percent
                    effect = "risk-reducing"
                else:
                    effect = "risk-increasing"

                clean_risk_contributions[k] = f"{round(percent, 2)}%"
                risk_effects[k] = effect
                chart_risk_contributions[k] = round(percent, 4)

        concentration = float(compute_concentration(raw_weights))
        diversification_ratio = float(
            compute_diversification_ratio(raw_weights, price_data)
        )

        simulated_returns = simulate_portfolio_annual_returns(
            weights=raw_weights,
            price_data=price_data,
            n_simulations=5000,
            random_seed=42,
        )

        simulation_summary = summarize_simulation_results(simulated_returns)
        simulation_chart_data = prepare_simulation_chart_data(simulated_returns)

        if diversification_ratio < 1.2:
            diversification_level = "low"
        elif diversification_ratio <= 1.5:
            diversification_level = "moderate"
        else:
            diversification_level = "strong"

        if concentration < 0.15:
            concentration_level = "low"
        elif concentration <= 0.25:
            concentration_level = "moderate"
        else:
            concentration_level = "high"

        feasible = None

        response = {
            "desired_return": f"{target_return:.2%}",
            "expected_portfolio_return": f"{portfolio_return:.2%}",
            "portfolio_volatility": f"{portfolio_volatility:.2%}",
            "weights_percent": clean_weights,
            "risk_contributions": clean_risk_contributions,
            "risk_effects": risk_effects,
            "diversification_ratio": round(diversification_ratio, 3),
            "diversification_level": diversification_level,
            "concentration_index": round(concentration, 3),
            "concentration_level": concentration_level,
            "simulation": {
                "mean_return": f"{simulation_summary['mean_return']:.2%}",
                "median_return": f"{simulation_summary['median_return']:.2%}",
                "loss_probability": f"{simulation_summary['loss_probability']:.2%}",
                "percentile_5": f"{simulation_summary['percentile_5']:.2%}",
                "percentile_95": f"{simulation_summary['percentile_95']:.2%}",
            },
            "chart_data": {
                "weights": chart_weights,
                "risk_contributions": chart_risk_contributions,
                "simulation_distribution": simulation_chart_data,
            },
        }

        if max_volatility is not None:
            feasible = bool(portfolio_volatility <= max_volatility + 1e-6)

            response["max_allowed_volatility"] = f"{max_volatility:.2%}"
            response["feasible"] = feasible
            response["message"] = (
                "Minimum-risk portfolio for the requested return constructed under the user's volatility constraint."
                if feasible
                else "The portfolio is slightly above the requested volatility limit due to solver tolerance."
            )
        else:
            response["message"] = (
                "Minimum-risk portfolio for the requested return."
            )

        explanation_bullets = generate_explanation_bullets(
            desired_return=target_return,
            expected_portfolio_return=portfolio_return,
            portfolio_volatility=portfolio_volatility,
            weights=raw_weights,
            risk_contributions=risk_contributions,
            diversification_ratio=diversification_ratio,
            concentration=concentration,
            feasible=feasible,
            max_weight_constraint=0.35,
            simulation_mean_return=simulation_summary["mean_return"],
            simulation_median_return=simulation_summary["median_return"],
            simulation_loss_probability=simulation_summary["loss_probability"],
            simulation_percentile_5=simulation_summary["percentile_5"],
            simulation_percentile_95=simulation_summary["percentile_95"],
        )

        response["explanation_bullets"] = explanation_bullets

        return response

    except ValueError as e:
        error_message = str(e).lower()

        if "maximum feasible return" in error_message:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}",
        )