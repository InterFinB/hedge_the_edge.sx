"use client";

import { useMemo, useState } from "react";

import {
  PortfolioForm,
  LoadingFacts,
  StatusBanner,
  PortfolioSummary,
  PortfolioSnapshot,
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
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto max-w-[1200px] space-y-8 px-6 py-12">
        <header className="mb-8 space-y-3">
          <h1 className="text-5xl font-semibold tracking-tight text-slate-900">
            Hedge the Edge
          </h1>

          <p className="max-w-3xl text-lg leading-relaxed text-slate-600">
            Generate a minimum-risk portfolio for a target return and review
            allocation, diagnostics, simulation, and explanation in one place.
          </p>
        </header>

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
          <div className="space-y-8">
            <StatusBanner
              desiredReturn={desiredReturn}
              maxReturn={result.max_return}
              volatility={result.portfolio_volatility}
              maxVolatility={parsePercentInput(maxVolatilityInput)}
            />

            <PortfolioSummary result={result} />

            <PortfolioSnapshot result={result} />

            <section className="grid gap-6 xl:grid-cols-2">
              <AllocationChart weights={result.weights} />
              <CategoryExposureChart weights={result.weights} />
            </section>

            <section className="grid gap-6 xl:grid-cols-2">
              <RiskContributionChart
                riskContributions={riskContributionEntries}
              />

              <SimulationDistributionChart
                simulationChart={result.simulation_chart}
              />
            </section>

            <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
              <WeightsTable weights={result.weights} />

              <DiagnosticsPanel
                concentration={result.concentration}
                diversificationRatio={result.diversification_ratio}
                meaningfulPositionsCount={result.meaningful_positions?.length}
                topRiskContributions={riskContributionEntries}
              />
            </section>

            <SimulationSummary result={result} />

            <ExplanationSection explanation={result.explanation} />
          </div>
        )}
      </div>
    </main>
  );
}