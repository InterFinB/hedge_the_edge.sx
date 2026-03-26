"use client";

import { useMemo, useState } from "react";

import {
  PortfolioForm,
  LoadingFacts,
  StatusBanner,
  PortfolioOverview,
  AllocationChart,
  CategoryExposureChart,
  RiskContributionChart,
  SimulationDistributionChart,
  SimulationSummary,
  WeightsTable,
  ExplanationSection,
  DiagnosticsPanel,
} from "@/components/ui";

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

export default function Home() {
  const [targetReturnInput, setTargetReturnInput] = useState("10");
  const [maxVolatilityInput, setMaxVolatilityInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PortfolioResponse | null>(null);

  const generate = async () => {
    setLoading(true);
    setError("");
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
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unknown error occurred";

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
                  allocation, diagnostics, simulation, and explanation in one place.
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

          {result && (
            <div className="space-y-4">
              <StatusBanner
                desiredReturn={desiredReturn}
                maxReturn={result.max_return}
                volatility={result.portfolio_volatility}
                maxVolatility={parsePercentInput(maxVolatilityInput)}
              />

              <PortfolioOverview result={result} />

              <section className="grid gap-4 xl:grid-cols-2">
                <AllocationChart
                  weights={result.weights}
                  tickerToName={result.ticker_to_name}
                />
                <CategoryExposureChart weights={result.weights} />
              </section>

              <section className="grid gap-4 xl:grid-cols-2">
                <RiskContributionChart
                  riskContributions={riskContributionEntries}
                />
                <SimulationDistributionChart
                  simulationChart={result.simulation_chart}
                />
              </section>

              <section className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
                <WeightsTable
                  weights={result.weights}
                  tickerToName={result.ticker_to_name}
                />
                <div className="grid gap-4">
                  <SimulationSummary result={result} />
                  <DiagnosticsPanel
                    concentration={result.concentration}
                    diversificationRatio={result.diversification_ratio}
                    meaningfulPositionsCount={result.meaningful_positions?.length}
                    topRiskContributions={riskContributionEntries}
                  />
                </div>
              </section>

              <ExplanationSection explanation={result.explanation} />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}