"use client";

import { useEffect, useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  AreaChart,
  Area,
} from "recharts";

/* =========================================================
   helpers
========================================================= */

function pct(x?: number | null, digits = 2) {
  if (x === undefined || x === null || Number.isNaN(x)) return "—";
  return `${(x * 100).toFixed(digits)}%`;
}

function num(x?: number | null, digits = 2) {
  if (x === undefined || x === null || Number.isNaN(x)) return "—";
  return x.toFixed(digits);
}

function Card({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="
        rounded-3xl
        border border-slate-200
        bg-white
        p-5
        shadow-sm
        transition
        hover:shadow-md
      "
    >
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {title}
      </div>

      <div className="mt-2 text-2xl font-semibold text-slate-900">
        {children}
      </div>
    </div>
  );
}

function Box({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className="
        rounded-3xl
        border border-slate-200
        bg-white
        p-6
        shadow-sm
        space-y-4
      "
    >
      <h2 className="text-xl font-semibold tracking-tight text-slate-900">
        {title}
      </h2>

      {children}
    </section>
  );
}

/* =========================================================
   investment facts / loading facts
========================================================= */

const FACTS = [
  "Diversification helps reduce single-asset risk, but it does not remove market risk.",
  "Volatility measures dispersion of returns, not whether an asset is good or bad.",
  "A target return can become infeasible when constraints are too tight.",
  "Risk contribution shows which holdings drive portfolio volatility the most.",
  "A portfolio with fewer meaningful positions may be easier to understand, but less diversified.",
  "Monte Carlo simulation shows a range of possible outcomes, not a guaranteed future.",
  "The highest-return portfolio is rarely the best fit for a real investor.",
  "A volatility cap can force the optimizer to sacrifice expected return.",
];

export function LoadingFacts() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % FACTS.length);
    }, 5000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="rounded-3xl border border-blue-100 bg-blue-50 p-5 shadow-sm">
      <div className="flex items-start gap-4">
        <div className="mt-1 h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-800" />
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
            Building your portfolio
          </p>
          <p className="mt-2 text-slate-700">{FACTS[index]}</p>
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   form
========================================================= */

export function PortfolioForm({
  targetReturnInput,
  setTargetReturnInput,
  maxVolatilityInput,
  setMaxVolatilityInput,
  loading,
  error,
  onSubmit,
}: {
  targetReturnInput: string;
  setTargetReturnInput: (value: string) => void;
  maxVolatilityInput: string;
  setMaxVolatilityInput: (value: string) => void;
  loading: boolean;
  error: string;
  onSubmit: () => void;
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Target return (%)
          </label>
          <input
            value={targetReturnInput}
            onChange={(e) => setTargetReturnInput(e.target.value)}
            placeholder="e.g. 10"
            className="w-full rounded-2xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500"
          />
          <p className="mt-2 text-sm text-slate-500">
            Enter a yearly target return like 8, 10, or 12.
          </p>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Max volatility (%) — optional
          </label>
          <input
            value={maxVolatilityInput}
            onChange={(e) => setMaxVolatilityInput(e.target.value)}
            placeholder="e.g. 15"
            className="w-full rounded-2xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500"
          />
          <p className="mt-2 text-sm text-slate-500">
            Leave blank if you do not want a volatility cap.
          </p>
        </div>
      </div>

      <div className="mt-6 flex items-center gap-4">
        <button
          onClick={onSubmit}
          disabled={loading}
          className="
            rounded-2xl
            bg-slate-900
            px-6 py-3
            font-medium
            text-white
            shadow-sm
            hover:bg-slate-800
            transition
            disabled:cursor-not-allowed
            disabled:opacity-60
          "
        >
          {loading ? "Generating portfolio..." : "Generate portfolio"}
        </button>
      </div>

      {error && (
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
          <p className="font-semibold">Request failed</p>
          <p className="mt-1 text-sm">{error}</p>
        </div>
      )}
    </section>
  );
}

/* =========================================================
   status banner
========================================================= */

export function StatusBanner({
  desiredReturn,
  maxReturn,
  volatility,
  maxVolatility,
}: {
  desiredReturn?: number;
  maxReturn?: number;
  volatility?: number;
  maxVolatility?: number | null;
}) {
  let title = "Portfolio generated";
  let text =
    "The optimizer found a portfolio under the current constraints.";
  let classes = "border-emerald-200 bg-emerald-50 text-emerald-800";

  if (
    desiredReturn !== undefined &&
    maxReturn !== undefined &&
    desiredReturn > maxReturn
  ) {
    title = "Target return exceeds feasible range";
    text = `Your requested return of ${pct(
      desiredReturn
    )} is above the current feasible maximum of ${pct(maxReturn)}.`;
    classes = "border-amber-200 bg-amber-50 text-amber-800";
  } else if (
    maxVolatility !== null &&
    maxVolatility !== undefined &&
    volatility !== undefined &&
    volatility > maxVolatility
  ) {
    title = "Volatility cap may be binding";
    text = `The portfolio volatility is ${pct(
      volatility
    )}, versus a cap of ${pct(maxVolatility)}.`;
    classes = "border-amber-200 bg-amber-50 text-amber-800";
  }

  return (
    <section className={`rounded-3xl border p-5 shadow-sm ${classes}`}>
      <p className="text-sm font-semibold uppercase tracking-wide">{title}</p>
      <p className="mt-2">{text}</p>
    </section>
  );
}

/* =========================================================
   summary
========================================================= */

export function PortfolioSummary({ result }: { result: any }) {
  const desiredReturn = result.desired_return ?? result.target_return;
  const expectedReturn =
    result.expected_portfolio_return ?? result.portfolio_return;

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card title="Target return">{pct(desiredReturn)}</Card>
      <Card title="Expected portfolio return">{pct(expectedReturn)}</Card>
      <Card title="Portfolio volatility">{pct(result.portfolio_volatility)}</Card>
      <Card title="Max feasible return">{pct(result.max_return)}</Card>
    </section>
  );
}

/* =========================================================
   snapshot
========================================================= */

export function PortfolioSnapshot({ result }: { result: any }) {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <Card title="Active positions">{result.active_positions ?? "—"}</Card>
      <Card title="Largest weight">{pct(result.largest_weight)}</Card>
      <Card title="Diversification ratio">
        {result.diversification_ratio !== undefined &&
        result.diversification_ratio !== null
          ? result.diversification_ratio.toFixed(2)
          : "—"}
      </Card>
      <Card title="Recompute interval">
        {typeof result.recompute_interval === "object"
          ? result.recompute_interval.interval_label
          : result.recompute_interval ??
            result.recompute_schedule ??
            "—"}
      </Card>
    </section>
  );
}

/* =========================================================
   allocation chart
========================================================= */

const PIE_COLORS = [
  "#0f172a",
  "#1d4ed8",
  "#0f766e",
  "#7c3aed",
  "#ea580c",
  "#0891b2",
  "#65a30d",
  "#db2777",
  "#475569",
  "#c2410c",
];

export function AllocationChart({ weights }: { weights: Record<string, number> }) {
  const data = Object.entries(weights)
    .filter(([_, w]) => w > 0.001)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({
      name,
      value: Number((value * 100).toFixed(2)),
    }));

  if (data.length === 0) return null;

  return (
    <Box title="Allocation chart">
      <div className="h-[380px] w-full">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={130}
              innerRadius={60}
              label={({ name, value }) => `${name} ${value}%`}
              labelLine={false}
            >
              {data.map((_, index) => (
                <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Box>
  );
}

/* =========================================================
   category exposure chart
========================================================= */

const TICKER_CATEGORY: Record<string, string> = {
  AAPL: "Technology",
  MSFT: "Technology",
  NVDA: "Technology",
  CSCO: "Technology",
  CRM: "Technology",

  JPM: "Financials",
  MS: "Financials",
  BLK: "Financials",
  XLF: "Financials",

  UNH: "Healthcare",
  ABBV: "Healthcare",

  WMT: "Consumer Defensive",
  NKE: "Consumer Cyclical",
  MO: "Consumer Defensive",

  CAT: "Industrials",
  GE: "Industrials",

  AMT: "Real Estate",
  PLD: "Real Estate",
  VNQ: "Real Estate",

  SLB: "Energy",
  APD: "Materials",

  DBC: "Commodities",
  EWU: "International Equity",
};

const CATEGORY_COLORS = [
  "#0f766e",
  "#1d4ed8",
  "#7c3aed",
  "#ea580c",
  "#65a30d",
  "#db2777",
  "#475569",
  "#0891b2",
];

export function CategoryExposureChart({
  weights,
}: {
  weights: Record<string, number>;
}) {
  const categoryTotals = Object.entries(weights).reduce<Record<string, number>>(
    (acc, [ticker, weight]) => {
      if (weight <= 0.001) return acc;
      const category = TICKER_CATEGORY[ticker] || "Other";
      acc[category] = (acc[category] || 0) + weight;
      return acc;
    },
    {}
  );

  const data = Object.entries(categoryTotals)
    .map(([name, value]) => ({
      name,
      value: Number((value * 100).toFixed(2)),
    }))
    .sort((a, b) => b.value - a.value);

  if (data.length === 0) return null;

  return (
    <Box title="Category exposure">
      <div className="h-[360px] w-full">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              outerRadius={125}
              label={({ name, value }) => `${name} ${value}%`}
              labelLine={false}
            >
              {data.map((_, index) => (
                <Cell
                  key={index}
                  fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Box>
  );
}

/* =========================================================
   risk contribution chart
========================================================= */

export function RiskContributionChart({
  riskContributions,
}: {
  riskContributions: { ticker: string; value: number }[];
}) {
  const data = riskContributions
    .filter((x) => x.value > 0.0001)
    .slice(0, 10)
    .map((x) => ({
      name: x.ticker,
      value: Number(x.value.toFixed(4)),
    }));

  if (data.length === 0) return null;

  return (
    <Box title="Risk contribution">
      <div className="h-[340px] w-full">
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#1d4ed8" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Box>
  );
}

/* =========================================================
   simulation distribution chart
========================================================= */

function normalizeSimulationChart(input: unknown) {
  if (Array.isArray(input)) {
    return input
      .map((item: any) => {
        const x =
          item.bin ??
          item.x ??
          item.return ??
          item.center ??
          item.label ??
          "";
        const y = item.count ?? item.frequency ?? item.y ?? item.value ?? 0;
        return {
          x: typeof x === "number" ? `${(x * 100).toFixed(1)}%` : String(x),
          y: Number(y),
        };
      })
      .filter((d) => !Number.isNaN(d.y));
  }

  if (
    input &&
    typeof input === "object" &&
    "bins" in (input as any) &&
    "counts" in (input as any)
  ) {
    const bins = (input as any).bins as Array<number | string>;
    const counts = (input as any).counts as number[];

    return bins.map((bin, idx) => ({
      x: typeof bin === "number" ? `${(bin * 100).toFixed(1)}%` : String(bin),
      y: Number(counts[idx] ?? 0),
    }));
  }

  return [];
}

export function SimulationDistributionChart({
  simulationChart,
}: {
  simulationChart: unknown;
}) {
  const data = useMemo(() => normalizeSimulationChart(simulationChart), [simulationChart]);

  if (data.length === 0) return null;

  return (
    <Box title="Simulation distribution">
      <div className="h-[340px] w-full">
        <ResponsiveContainer>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="x" minTickGap={20} />
            <YAxis />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="y"
              stroke="#0f766e"
              fill="#99f6e4"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Box>
  );
}

/* =========================================================
   simulation summary
========================================================= */

export function SimulationSummary({ result }: { result: any }) {
  const s = result.simulation_summary;
  const compact = result.simulation;

  return (
    <Box title="Simulation outlook">
      <p className="mb-6 text-slate-600">
        Summary of the simulated annual return distribution.
      </p>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Card title="Mean return">{pct(s?.mean_return ?? compact?.mean)}</Card>
        <Card title="Median return">{pct(s?.median_return ?? compact?.median)}</Card>
        <Card title="Loss probability">
          {pct(s?.loss_probability ?? compact?.loss_probability)}
        </Card>
        <Card title="5th percentile">
          {pct(s?.percentile_5 ?? compact?.p5)}
        </Card>
        <Card title="95th percentile">
          {pct(s?.percentile_95 ?? compact?.p95)}
        </Card>
      </div>
    </Box>
  );
}

/* =========================================================
   weights table
========================================================= */

export function WeightsTable({ weights }: { weights: Record<string, number> }) {
  const rows = Object.entries(weights)
    .filter(([_, v]) => v > 0.001)
    .sort((a, b) => b[1] - a[1]);

  return (
    <Box title="Portfolio allocation">
      <p className="mb-4 text-slate-600">Only meaningful positions are shown.</p>

      <div className="space-y-2">
        {rows.map(([ticker, weight]) => (
          <div
            key={ticker}
            className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3"
          >
            <span className="font-medium text-slate-900">{ticker}</span>
            <span className="text-slate-700">{pct(weight)}</span>
          </div>
        ))}
      </div>
    </Box>
  );
}

/* =========================================================
   explanation
========================================================= */

function extractExplanationSections(explanation: any) {
  if (!explanation) {
    return {
      summary: "",
      watchFor: [] as string[],
      takeaways: [] as string[],
      vocabulary: [] as Array<{ term: string; definition: string }>,
    };
  }

  if (typeof explanation === "string") {
    return {
      summary: explanation,
      watchFor: [],
      takeaways: [],
      vocabulary: [],
    };
  }

  const summary =
    typeof explanation.summary === "string" ? explanation.summary : "";

  const watchFor = Array.isArray(explanation.watch_for)
    ? explanation.watch_for.map(String)
    : typeof explanation.watch_for === "string"
    ? [explanation.watch_for]
    : [];

  const takeaways = Array.isArray(explanation.takeaways)
    ? explanation.takeaways.map(String)
    : typeof explanation.takeaways === "string"
    ? [explanation.takeaways]
    : [];

  let vocabulary: Array<{ term: string; definition: string }> = [];

  if (
    explanation.vocabulary &&
    typeof explanation.vocabulary === "object" &&
    !Array.isArray(explanation.vocabulary)
  ) {
    vocabulary = Object.entries(explanation.vocabulary).map(
      ([term, definition]) => ({
        term,
        definition: String(definition),
      })
    );
  } else if (Array.isArray(explanation.vocabulary)) {
    vocabulary = explanation.vocabulary.map((item: any, index: number) => ({
      term: `Term ${index + 1}`,
      definition: String(item),
    }));
  } else if (typeof explanation.vocabulary === "string") {
    vocabulary = [{ term: "Vocabulary", definition: explanation.vocabulary }];
  }

  return { summary, watchFor, takeaways, vocabulary };
}

export function ExplanationSection({ explanation }: { explanation: any }) {
  const sections = extractExplanationSections(explanation);

  return (
    <div className="space-y-8">
      <section className="grid gap-6 xl:grid-cols-2">
        <Box title="Explanation">
          <p className="whitespace-pre-wrap leading-7 text-slate-700">
            {sections.summary || "No explanation summary available yet."}
          </p>
        </Box>

        <div className="space-y-8">
          <Box title="What to watch for">
            {sections.watchFor.length > 0 ? (
              <div className="space-y-3">
                {sections.watchFor.map((item, index) => (
                  <div
                    key={`${item}-${index}`}
                    className="rounded-2xl bg-slate-50 p-4 text-slate-700"
                  >
                    {item}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500">No watch-for items available yet.</p>
            )}
          </Box>

          <Box title="Takeaways">
            {sections.takeaways.length > 0 ? (
              <div className="space-y-3">
                {sections.takeaways.map((item, index) => (
                  <div
                    key={`${item}-${index}`}
                    className="rounded-2xl bg-slate-50 p-4 text-slate-700"
                  >
                    {item}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500">No takeaways available yet.</p>
            )}
          </Box>
        </div>
      </section>

      <Box title="Vocabulary">
        {sections.vocabulary.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2">
            {sections.vocabulary.map((item) => (
              <div key={item.term} className="rounded-2xl bg-slate-50 p-4">
                <p className="font-semibold text-slate-900">{item.term}</p>
                <p className="mt-2 leading-7 text-slate-700">{item.definition}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-500">No vocabulary items available yet.</p>
        )}
      </Box>

      <Box title="Important assumptions">
        <div className="space-y-3 text-slate-700">
          <div className="rounded-2xl bg-slate-50 p-4">
            The optimizer uses historical-data-derived estimates and current constraints.
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            Simulation output describes a range of possible outcomes, not a guaranteed forecast.
          </div>
          <div className="rounded-2xl bg-slate-50 p-4">
            Real-world results can differ because of regime changes, transaction costs, and data limitations.
          </div>
        </div>
      </Box>
    </div>
  );
}

/* =========================================================
   diagnostics block
========================================================= */

export function DiagnosticsPanel({
  concentration,
  diversificationRatio,
  meaningfulPositionsCount,
  topRiskContributions,
}: {
  concentration?: number;
  diversificationRatio?: number;
  meaningfulPositionsCount?: number;
  topRiskContributions: { ticker: string; value: number }[];
}) {
  return (
    <div className="space-y-8">
      <Box title="Risk diagnostics">
        <div className="space-y-4">
          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Concentration</p>
            <p className="mt-1 text-xl font-semibold">{num(concentration, 4)}</p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Diversification ratio</p>
            <p className="mt-1 text-xl font-semibold">
              {num(diversificationRatio, 4)}
            </p>
          </div>

          <div className="rounded-2xl bg-slate-50 p-4">
            <p className="text-sm text-slate-500">Meaningful positions</p>
            <p className="mt-1 text-xl font-semibold">
              {meaningfulPositionsCount ?? "—"}
            </p>
          </div>
        </div>
      </Box>

      <Box title="Top risk contributors">
        <div className="space-y-3">
          {topRiskContributions.slice(0, 6).map((item) => (
            <div
              key={item.ticker}
              className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3"
            >
              <span className="font-medium">{item.ticker}</span>
              <span className="text-slate-700">{item.value.toFixed(4)}</span>
            </div>
          ))}

          {topRiskContributions.length === 0 && (
            <p className="text-slate-500">No risk contribution data available.</p>
          )}
        </div>
      </Box>
    </div>
  );
}