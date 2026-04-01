from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class PortfolioObjective(BaseModel):
    target_return: float
    target_return_percent: float
    max_volatility: float | None = None
    max_volatility_percent: float | None = None


class PortfolioOutcome(BaseModel):
    expected_return: float
    expected_return_percent: float
    volatility: float
    volatility_percent: float
    active_positions: int
    largest_weight: float
    largest_weight_percent: float
    diversification_ratio: float
    concentration: float
    pre_prune_assets: int | None = None
    post_prune_assets: int | None = None
    concentration_threshold_used: float | None = None
    concentration_capped: bool = False


class TopPositionDatum(BaseModel):
    ticker: str
    name: str | None = None
    category: str | None = None
    weight: float
    weight_percent: float | None = None


class CategoryExposureDatum(BaseModel):
    category: str
    weight: float
    weight_percent: float | None = None


class RiskContributorDatum(BaseModel):
    ticker: str
    name: str | None = None
    category: str | None = None
    risk_contribution: float | None = None


class SimulationSummaryData(BaseModel):
    mean_return: float
    median_return: float
    loss_probability: float
    percentile_5: float
    percentile_95: float


class UniverseStatus(BaseModel):
    configured_count: int | None = None
    requested_count: int | None = None
    surviving_count: int | None = None
    effective_universe_count: int | None = None
    auto_pruned_count: int | None = None
    auto_pruned_tickers: list[str] = Field(default_factory=list)
    currently_auto_pruned_tickers: list[str] = Field(default_factory=list)
    newly_auto_pruned_tickers: list[str] = Field(default_factory=list)
    dropped_after_cleaning: list[str] = Field(default_factory=list)
    final_missing_tickers: list[str] = Field(default_factory=list)
    cache_status: str | None = None
    cache_warning: str | None = None
    refresh_summary: str | None = None


class AIContext(BaseModel):
    portfolio_objective: PortfolioObjective
    portfolio_outcome: PortfolioOutcome
    top_positions: list[TopPositionDatum] = Field(default_factory=list)
    top_categories: list[CategoryExposureDatum] = Field(default_factory=list)
    top_risk_contributors: list[RiskContributorDatum] = Field(default_factory=list)
    simulation: SimulationSummaryData
    universe_status: UniverseStatus
    market_data: dict[str, Any] = Field(default_factory=dict)
    explanation: dict[str, Any] | str | None = None
    selection_context: None = None


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskPortfolioRequest(BaseModel):
    question: str
    ai_context: AIContext
    conversation: list[ConversationTurn] = Field(default_factory=list)


class AskPortfolioResponse(BaseModel):
    answer: str
    reasoning_summary: list[str] = Field(default_factory=list)
    watch_for: list[str] = Field(default_factory=list)
    follow_up_suggestions: list[str] = Field(default_factory=list)
    source: str | None = None
    prompt_version: str | None = None