export type SimulationSummaryData = {
  mean_return?: number;
  median_return?: number;
  loss_probability?: number;
  percentile_5?: number;
  percentile_95?: number;
};

export type SimulationCompact = {
  mean?: number;
  median?: number;
  loss_probability?: number;
  p5?: number;
  p95?: number;
};

export type ExplanationBlock =
  | string
  | {
      portfolio_summary?: string[] | string;
      risk_commentary?: string[] | string;
      simulation_commentary?: string[] | string;
      watch_for?: string | string[];
      takeaways?: string | string[];
      vocabulary?: Record<string, string> | string[] | string;
      [key: string]: unknown;
    };

export type ChartDatum = {
  ticker?: string;
  weight?: number;
  name?: string;
  value?: number;
  bin?: number | string;
  count?: number;
  frequency?: number;
  x?: number | string;
  y?: number;
  [key: string]: unknown;
};

export type CategoryExposureDatum = {
  category: string;
  weight: number;
  weight_percent?: number;
};

export type TopPositionDatum = {
  ticker: string;
  name?: string;
  category?: string;
  weight: number;
  weight_percent?: number;
};

export type RiskContributorDatum = {
  ticker: string;
  name?: string;
  category?: string;
  risk_contribution?: number;
};

export type PortfolioTiming = {
  load_cached_market_state_seconds?: number;
  compute_max_return_seconds?: number;
  optimization_seconds?: number;
  portfolio_metrics_seconds?: number;
  simulation_seconds?: number;
  response_structuring_seconds?: number;
  explanation_seconds?: number;
  total_portfolio_request_seconds?: number;
};

export type UniverseStatus = {
  configured_count?: number;
  requested_count?: number;
  surviving_count?: number;
  effective_universe_count?: number;
  auto_pruned_count?: number;
  auto_pruned_tickers?: string[];
  currently_auto_pruned_tickers?: string[];
  newly_auto_pruned_tickers?: string[];
  dropped_after_cleaning?: string[];
  final_missing_tickers?: string[];
  cache_status?: string;
  cache_warning?: string | null;
  refresh_summary?: string | null;
};

export type ExplanationInputBlock = {
  portfolio_objective?: {
    target_return?: number;
    target_return_percent?: number;
    max_volatility?: number | null;
    max_volatility_percent?: number | null;
  };
  portfolio_outcome?: {
    expected_return?: number;
    expected_return_percent?: number;
    volatility?: number;
    volatility_percent?: number;
    active_positions?: number;
    largest_weight?: number;
    largest_weight_percent?: number;
    diversification_ratio?: number;
    concentration?: number;
    pre_prune_assets?: number;
    post_prune_assets?: number;
    concentration_threshold_used?: number;
    concentration_capped?: boolean;
  };
  top_positions?: TopPositionDatum[];
  top_categories?: CategoryExposureDatum[];
  top_risk_contributors?: RiskContributorDatum[];
  simulation?: SimulationSummaryData;
  universe_status?: UniverseStatus;
  market_data?: unknown;
};

export type MarketDataMetadata = {
  configured_tickers?: string[] | null;
  configured_count?: number;
  auto_pruned_tickers?: string[] | null;
  auto_pruned_count?: number;
  requested_tickers?: string[] | null;
  requested_count?: number;
  initial_missing_tickers?: string[] | null;
  recovered_tickers?: string[] | null;
  final_missing_tickers?: string[] | null;
  dropped_after_cleaning?: string[] | null;
  final_tickers?: string[] | null;
  surviving_count?: number;
  summary?: string | null;
};

export type MarketDataStatus = {
  cache_status?: "fresh" | "stale_fallback" | "stale_cached" | "unknown";
  cache_timestamp?: string | null;
  warning?: string | null;
  data_metadata?: MarketDataMetadata | null;
  num_assets?: number;
  tickers?: string[];
};

export type AIContext = {
  portfolio_objective: {
    target_return: number;
    target_return_percent: number;
    max_volatility?: number | null;
    max_volatility_percent?: number | null;
  };
  portfolio_outcome: {
    expected_return: number;
    expected_return_percent: number;
    volatility: number;
    volatility_percent: number;
    active_positions: number;
    largest_weight: number;
    largest_weight_percent: number;
    diversification_ratio: number;
    concentration: number;
    pre_prune_assets?: number | null;
    post_prune_assets?: number | null;
    concentration_threshold_used?: number | null;
    concentration_capped: boolean;
  };
  top_positions: TopPositionDatum[];
  top_categories: CategoryExposureDatum[];
  top_risk_contributors: RiskContributorDatum[];
  simulation: {
    mean_return: number;
    median_return: number;
    loss_probability: number;
    percentile_5: number;
    percentile_95: number;
  };
  universe_status: UniverseStatus;
  market_data: Record<string, unknown>;
  explanation?: ExplanationBlock | null;
  selection_context?: null;
};

export type AskPortfolioRequest = {
  question: string;
  ai_context: AIContext;
  conversation?: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
};

export type AskPortfolioResponse = {
  answer: string;
  reasoning_summary: string[];
  watch_for: string[];
  follow_up_suggestions: string[];
  source?: string | null;
  prompt_version?: string | null;
};

export type PortfolioResponse = {
  desired_return?: number;
  target_return?: number;
  expected_portfolio_return?: number;
  portfolio_return?: number;
  portfolio_volatility: number;
  max_return?: number;
  weights: Record<string, number>;
  weights_percent?: Record<string, number>;
  tickers?: string[];
  ticker_to_name?: Record<string, string>;
  ticker_to_category?: Record<string, string>;
  chart_data?: ChartDatum[];
  category_exposure?: CategoryExposureDatum[];
  top_positions?: TopPositionDatum[];
  risk_effects?: Record<string, number> | number[];
  risk_contributions: Record<string, number> | number[];
  concentration?: number;
  diversification_ratio?: number;
  active_positions?: number;
  meaningful_positions?: string[];
  largest_weight?: number;
  pre_prune_assets?: number;
  post_prune_assets?: number;
  concentration_threshold_used?: number;
  concentration_capped?: boolean;
  recompute_interval?: string | number | { interval_label?: string };
  recompute_schedule?: string | number;
  simulation?: SimulationCompact;
  simulation_summary?: SimulationSummaryData;
  simulation_chart?: unknown;
  portfolio_timing?: PortfolioTiming;
  universe_status?: UniverseStatus;
  explanation_input?: ExplanationInputBlock;
  explanation?: ExplanationBlock;
  market_data?: MarketDataStatus;
  ai_context?: AIContext;
};