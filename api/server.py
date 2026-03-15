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
from portfolio_engine.risk import compute_portfolio_volatility, compute_portfolio_return
from portfolio_engine.input_parser import parse_percentage_input
from portfolio_engine.diagnostics import (
    compute_risk_contributions,
    compute_concentration,
    compute_diversification_ratio,
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
        "cache_loaded": data_loader._cached_price_data is not None
    }


@app.post("/refresh-data")
def refresh_data():
    price_data = load_price_data(force_refresh=True)
    return {
        "message": "Market data cache refreshed successfully.",
        "rows": len(price_data),
        "columns": len(price_data.columns)
    }


@app.post("/portfolio")
def generate_portfolio(request: PortfolioRequest):
    try:
        target_return = float(parse_percentage_input(request.target_return))

        price_data = load_price_data()
        weights = optimize_portfolio(target_return, price_data)

        portfolio_volatility = float(compute_portfolio_volatility(weights, price_data))
        portfolio_return = float(compute_portfolio_return(weights, price_data))

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
        diversification_ratio = float(compute_diversification_ratio(raw_weights, price_data))

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
            "chart_data": {
                "weights": chart_weights,
                "risk_contributions": chart_risk_contributions,
            },
        }

        if request.max_volatility is not None and request.max_volatility.strip() != "":
            max_volatility = float(parse_percentage_input(request.max_volatility))
            feasible = bool(portfolio_volatility <= max_volatility)

            response["max_allowed_volatility"] = f"{max_volatility:.2%}"
            response["feasible"] = feasible
            response["message"] = (
                "This portfolio satisfies the user's downside tolerance."
                if feasible
                else "This portfolio exceeds the user's downside tolerance."
            )
        else:
            response["message"] = "Minimum-risk portfolio for the requested return."

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
        )

        response["explanation_bullets"] = explanation_bullets

        return response

    except ValueError as e:
        error_message = str(e)

        if "target_return must be lower than the maximum possible return" in error_message:
            raise HTTPException(
                status_code=400,
                detail="The desired return is too high for the current investable universe. Please enter a lower target return."
            )

        raise HTTPException(status_code=400, detail=error_message)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {str(e)}")