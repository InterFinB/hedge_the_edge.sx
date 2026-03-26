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
      summary?: string;
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
  chart_data?: ChartDatum[];

  risk_effects?: Record<string, number> | number[];
  risk_contributions: Record<string, number> | number[];

  concentration?: number;
  diversification_ratio?: number;

  active_positions?: number;
  meaningful_positions?: string[];
  largest_weight?: number;

  recompute_interval?: string | number | { interval_label?: string };
  recompute_schedule?: string | number;

  simulation?: SimulationCompact;
  simulation_summary?: SimulationSummaryData;
  simulation_chart?: unknown;

  explanation?: ExplanationBlock;
};