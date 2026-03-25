from fastapi import FastAPI, HTTPException
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
    optimize_min_variance_portfolio,
)
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
from portfolio_engine.recompute_schedule import get_recompute_schedule
from explanation_layer import generate_explanation

app = FastAPI(title="RM Agent API")

DISPLAY_WEIGHT_THRESHOLD = 0.008
MEANINGFUL_WEIGHT_THRESHOLD = 0.008
MIN_PORTFOLIO_WEIGHT = 0.008
MAX_FINAL_HOLDINGS = 17


class PortfolioRequest(BaseModel):
    target_return: str
    max_volatility: Optional[str] = None


def prune_and_renormalize_weights(
    weights: dict,
    min_weight: float = MIN_PORTFOLIO_WEIGHT,
) -> dict:
    pruned = {
        k: float(v)
        for k, v in weights.items()
        if float(v) >= min_weight
    }

    total = sum(pruned.values())

    if total <= 0:
        raise ValueError("All portfolio weights were removed by the minimum weight threshold.")

    return {
        k: float(v) / total
        for k, v in pruned.items()
    }


def select_top_holdings(weights: dict, max_holdings: int = MAX_FINAL_HOLDINGS) -> list[str]:
    ranked = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    return [ticker for ticker, _ in ranked[:max_holdings]]


@app.get("/")
def home():
    return {"message": "RM Agent API is running"}


@app.get("/cache-status")
def cache_status():
    return {
        "cache_timestamp": str(data_loader._cache_timestamp),
        "cache_loaded": data_loader._cached_price_data is not None,
    }


@app.get("/return-range")
def get_return_range():
    try:
        market_state = load_market_state(force_refresh=False)
        price_data = market_state["price_data"]
        expected_returns = market_state["expected_returns"]
        cov_matrix = market_state["cov_matrix"]

        min_var_weights = optimize_min_variance_portfolio(
            price_data=price_data,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
        )

        min_feasible_return = compute_portfolio_return(min_var_weights, expected_returns)
        max_feasible_return = compute_max_feasible_return(expected_returns)

        return {
            "min_feasible_return": f"{min_feasible_return:.2%}",
            "max_feasible_return": f"{max_feasible_return:.2%}",
            "min_feasible_return_raw": float(min_feasible_return),
            "max_feasible_return_raw": float(max_feasible_return),
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}",
        )


@app.post("/refresh-data")
def refresh_data():
    market_state = load_market_state(force_refresh=True)
    price_data = market_state["price_data"]

    return {
        "message": "Market data cache refreshed successfully.",
        "rows": len(price_data),
        "columns": len(price_data.columns),
        "cache_timestamp": str(market_state["cache_timestamp"]),
    }


@app.post("/portfolio")
def generate_portfolio(request: PortfolioRequest):
    try:
        target_return = float(parse_percentage_input(request.target_return))

        max_volatility = None
        if request.max_volatility is not None and request.max_volatility.strip() != "":
            max_volatility = float(parse_percentage_input(request.max_volatility))

        market_state = load_market_state(force_refresh=False)
        price_data = market_state["price_data"]
        expected_returns = market_state["expected_returns"]
        cov_matrix = market_state["cov_matrix"]

        initial_weights = optimize_portfolio(
            target_return=target_return,
            price_data=price_data,
            max_volatility=max_volatility,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
        )

        initial_weights = {
            k: float(v)
            for k, v in dict(initial_weights).items()
        }

        pruned_weights = prune_and_renormalize_weights(
            initial_weights,
            MIN_PORTFOLIO_WEIGHT,
        )

        final_weights = pruned_weights

        if len(pruned_weights) > MAX_FINAL_HOLDINGS:
            reduced_assets = select_top_holdings(pruned_weights, MAX_FINAL_HOLDINGS)

            try:
                reduced_weights = optimize_portfolio(
                    target_return=target_return,
                    price_data=price_data,
                    max_volatility=max_volatility,
                    expected_returns=expected_returns.loc[reduced_assets],
                    cov_matrix=cov_matrix.loc[reduced_assets, reduced_assets],
                    asset_subset=reduced_assets,
                )

                final_weights = prune_and_renormalize_weights(
                    reduced_weights,
                    MIN_PORTFOLIO_WEIGHT,
                )

            except Exception:
                final_weights = pruned_weights

        raw_weights = final_weights

        portfolio_volatility = float(compute_portfolio_volatility(raw_weights, cov_matrix))
        portfolio_return = float(compute_portfolio_return(raw_weights, expected_returns))
        recompute_schedule = get_recompute_schedule(portfolio_volatility)

        active_positions = len(raw_weights)
        meaningful_positions = sum(
            1 for v in raw_weights.values() if v >= MEANINGFUL_WEIGHT_THRESHOLD
        )
        largest_weight = max(raw_weights.values()) if raw_weights else 0.0

        chart_weights = {
            k: float(v)
            for k, v in raw_weights.items()
            if v >= DISPLAY_WEIGHT_THRESHOLD
        }

        weights_percent = {
            k: round(v * 100, 4)
            for k, v in chart_weights.items()
        }

        risk_contributions = compute_risk_contributions(raw_weights, cov_matrix)
        total_absolute_risk = sum(abs(v) for v in risk_contributions.values())

        risk_contributions_percent = {}
        risk_effects = {}
        chart_risk_contributions = {}

        if total_absolute_risk != 0:
            for k, v in risk_contributions.items():
                if raw_weights.get(k, 0) < DISPLAY_WEIGHT_THRESHOLD:
                    continue

                percent = (abs(v) / total_absolute_risk) * 100
                effect = "risk-reducing" if v < 0 else "risk-increasing"

                if v < 0:
                    percent = -percent

                risk_contributions_percent[k] = round(percent, 4)
                risk_effects[k] = effect
                chart_risk_contributions[k] = round(percent, 4)

        concentration = float(compute_concentration(raw_weights))
        diversification_ratio = float(compute_diversification_ratio(raw_weights, cov_matrix))

        simulated_returns = simulate_portfolio_annual_returns(
            weights=raw_weights,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            n_simulations=1000,
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
            "recompute_interval": recompute_schedule.interval_label,
            "active_positions": active_positions,
            "meaningful_positions": meaningful_positions,
            "largest_weight": f"{largest_weight:.2%}",
            "weights_percent": weights_percent,
            "risk_contributions": risk_contributions_percent,
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
            response["message"] = "Minimum-risk portfolio for the requested return."

        explanation = generate_explanation(
            desired_return=target_return,
            expected_portfolio_return=portfolio_return,
            portfolio_volatility=portfolio_volatility,
            weights=raw_weights,
            risk_contributions=risk_contributions,
            diversification_ratio=diversification_ratio,
            concentration=concentration,
            feasible=feasible,
            max_volatility=max_volatility,
            max_weight_constraint=0.35,
            simulation_mean_return=simulation_summary["mean_return"],
            simulation_median_return=simulation_summary["median_return"],
            simulation_loss_probability=simulation_summary["loss_probability"],
            simulation_percentile_5=simulation_summary["percentile_5"],
            simulation_percentile_95=simulation_summary["percentile_95"],
        )

        response["explanation"] = explanation
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}",
        )