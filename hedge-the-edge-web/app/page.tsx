"use client";

import { useMemo, useState } from "react";

import {
  PortfolioForm,
  LoadingFacts,
  StatusBanner,
  PortfolioOverview,
  PortfolioStatusNote,
  AllocationChart,
  CategoryExposureChart,
  TopPositionsPanel,
  RiskContributionChart,
  SimulationDistributionChart,
  SimulationSummary,
  WeightsTable,
  ExplanationSection,
  DiagnosticsPanel,
} from "@/components/ui";

import PortfolioAskBar from "@/components/PortfolioAskBar";
import { generatePortfolio } from "@/services/api";
import type { PortfolioResponse } from "@/types/portfolio";

function parsePercentInput(input: string): number | null {
  const trimmed = input.trim();
  if (!trimmed) return null;

  const numeric = Number(trimmed.replace("%", ""));
  if (Number.isNaN(numeric)) return null;

  return numeric / 100;
}

function toRiskContributionEntries(
  riskContributions: PortfolioResponse["risk_contributions"],
  weights: Record<string, number>
) {
  if (Array.isArray(riskContributions)) {
    const tickers = Object.keys(weights);

    return tickers.map((ticker, index) => ({
      ticker,
      value: Number(riskContributions[index] ?? 0),
    }));
  }

  return Object.entries(riskContributions || {}).map(([ticker, value]) => ({
    ticker,
    value: Number(value),
  }));
}

function getReadableErrorMessage(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Unknown error occurred.";
  }

  const raw = error.message || "Unknown error occurred.";
  const lower = raw.toLowerCase();

  if (
    lower.includes("503") ||
    lower.includes("market data unavailable") ||
    lower.includes("unable to load market data") ||
    lower.includes("failed to download") ||
    lower.includes("no cached data is available")
  ) {
    return "Market data is temporarily unavailable. Please try again shortly.";
  }

  return raw;
}

function getReadableWarningMessage(warning?: string | null): string {
  if (!warning) return "";

  const lower = warning.toLowerCase();

  if (lower.includes("stale cached market data")) {
    return "Using cached market data because live refresh failed.";
  }

  if (lower.includes("missing")) {
    return "Some assets were unavailable during the latest market-data refresh.";
  }

  return warning;
}

export default function Home() {
  const [targetReturnInput, setTargetReturnInput] = useState("");
  const [maxVolatilityInput, setMaxVolatilityInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [result, setResult] = useState<PortfolioResponse | null>(null);

  const generate = async () => {
    setLoading(true);
    setError("");
    setWarning("");
    setResult(null);

    try {
      const targetReturn = parsePercentInput(targetReturnInput);
      const maxVolatility = parsePercentInput(maxVolatilityInput);

      if (targetReturn === null) {
        throw new Error("Please enter a valid target return percentage.");
      }

      const data = await generatePortfolio({
        target_return: targetReturn,
        max_volatility: maxVolatility,
      });

      setResult(data);

      const backendWarning =
        typeof data?.market_data?.warning === "string"
          ? data.market_data.warning
          : "";

      setWarning(getReadableWarningMessage(backendWarning));
    } catch (err) {
      const message = getReadableErrorMessage(err);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const riskContributionEntries = useMemo(() => {
    if (!result) return [];

    return toRiskContributionEntries(result.risk_contributions, result.weights)
      .filter((x) => x.value > 0.0001)
      .sort((a, b) => b.value - a.value);
  }, [result]);

  const desiredReturn = result?.desired_return ?? result?.target_return;
  const marketData = result?.market_data;

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f8fafc_0%,#eef2f7_45%,#e5ebf3_100%)] text-slate-900">
      <div className="mx-auto max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6">
          <div className="rounded-[28px] border border-white/70 bg-white/80 px-6 py-5 shadow-[0_10px_30px_rgba(15,23,42,0.06)] backdrop-blur">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                  Portfolio intelligence
                </p>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
                  Hedge the Edge
                </h1>
                <p className="max-w-3xl text-sm leading-6 text-slate-600 sm:text-[15px]">
                  Generate a minimum-risk portfolio for a target return and review
                  allocation, diagnostics, simulation, explanation, and AI Q&amp;A in
                  one place.
                </p>
              </div>

              <div className="inline-flex items-center rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                <span className="mr-2 h-2 w-2 rounded-full bg-emerald-500" />
                <span className="font-medium text-slate-900">Dashboard mode:</span>
                <span className="ml-1">compact</span>
              </div>
            </div>
          </div>
        </header>

        <div className="space-y-4">
          <PortfolioForm
            targetReturnInput={targetReturnInput}
            setTargetReturnInput={setTargetReturnInput}
            maxVolatilityInput={maxVolatilityInput}
            setMaxVolatilityInput={setMaxVolatilityInput}
            loading={loading}
            error={error}
            onSubmit={generate}
          />

          {loading && <LoadingFacts />}

          {warning && !loading && (
            <div className="rounded-[24px] border border-amber-200 bg-amber-50/90 px-5 py-4 text-sm text-amber-900 shadow-[0_10px_25px_rgba(15,23,42,0.04)]">
              <div className="font-semibold">Market data notice</div>
              <p className="mt-1 leading-6">{warning}</p>
            </div>
          )}

          {marketData && !loading && !error && (
            <div className="rounded-[24px] border border-slate-200 bg-white/80 px-5 py-4 text-sm text-slate-700 shadow-[0_10px_25px_rgba(15,23,42,0.04)] backdrop-blur">
              <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-6">
                <div>
                  <span className="font-semibold text-slate-900">Cache status:</span>{" "}
                  {marketData.cache_status ?? "unknown"}
                </div>

                <div>
                  <span className="font-semibold text-slate-900">
                    Assets available:
                  </span>{" "}
                  {marketData.num_assets ?? result?.tickers?.length ?? 0}
                </div>

                {marketData.cache_timestamp && (
                  <div>
                    <span className="font-semibold text-slate-900">Updated:</span>{" "}
                    {marketData.cache_timestamp}
                  </div>
                )}
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <StatusBanner
                desiredReturn={desiredReturn}
                maxReturn={result.max_return}
                volatility={result.portfolio_volatility}
                maxVolatility={parsePercentInput(maxVolatilityInput)}
              />

              <PortfolioOverview result={result} />

              <PortfolioStatusNote
                universeStatus={result.universe_status}
                marketData={result.market_data}
              />

              <section className="grid gap-4 xl:grid-cols-2">
                <AllocationChart
                  weights={result.weights}
                  tickerToName={result.ticker_to_name}
                />
                <CategoryExposureChart
                  categoryExposure={result.category_exposure}
                />
              </section>

              <section className="grid gap-4 xl:grid-cols-2">
                <TopPositionsPanel topPositions={result.top_positions} />
                <RiskContributionChart
                  riskContributions={riskContributionEntries}
                />
              </section>

              <section className="grid gap-4 xl:grid-cols-2">
                <SimulationDistributionChart
                  simulationChart={result.simulation_chart}
                />
                <SimulationSummary result={result} />
              </section>

              <ExplanationSection explanation={result.explanation} />

              <PortfolioAskBar
                aiContext={result.ai_context ?? null}
                explanation={result.explanation}
                disabled={loading}
              />

              <section className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
                <WeightsTable
                  weights={result.weights}
                  tickerToName={result.ticker_to_name}
                />
                <DiagnosticsPanel
                  concentration={result.concentration}
                  diversificationRatio={result.diversification_ratio}
                  meaningfulPositionsCount={result.meaningful_positions?.length}
                  topRiskContributions={riskContributionEntries}
                  prePruneAssets={result.pre_prune_assets}
                  postPruneAssets={result.post_prune_assets}
                  concentrationThresholdUsed={result.concentration_threshold_used}
                  concentrationCapped={result.concentration_capped}
                />
              </section>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}