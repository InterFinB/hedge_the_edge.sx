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

function tickerName(t: string, tickerToName?: Record<string, string>) {
  return tickerToName?.[t] || t;
}

function compactTooltipFormatter(value: unknown, suffix = "%", digits = 2) {
  return typeof value === "number"
    ? `${value.toFixed(digits)}${suffix}`
    : String(value ?? "");
}

function Box({
  title,
  children,
  rightSlot,
}: {
  title: string;
  children: React.ReactNode;
  rightSlot?: React.ReactNode;
}) {
  return (
    <section className="rounded-[26px] border border-white/70 bg-white/88 p-4 shadow-[0_8px_28px_rgba(15,23,42,0.06)] backdrop-blur">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          {title}
        </h2>
        {rightSlot ? <div>{rightSlot}</div> : null}
      </div>
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
    <section className="rounded-[28px] border border-white/70 bg-white/88 p-6 shadow-[0_8px_28px_rgba(15,23,42,0.06)] backdrop-blur">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            Portfolio inputs
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Set return and optional volatility guardrails.
          </p>
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Target return (%)
          </label>
          <input
            type="text"
            inputMode="decimal"
            name="target-return-field"
            autoComplete="off"
            value={targetReturnInput}
            onChange={(e) => setTargetReturnInput(e.target.value)}
            placeholder="e.g. 10"
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
          />
          <p className="mt-2 text-xs text-slate-500">
            Enter a yearly target return like 8, 10, or 12.
          </p>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-700">
            Max volatility (%) — optional
          </label>
          <input
            type="text"
            inputMode="decimal"
            name="max-volatility-field"
            autoComplete="off"
            value={maxVolatilityInput}
            onChange={(e) => setMaxVolatilityInput(e.target.value)}
            placeholder="e.g. 15"
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
          />
          <p className="mt-2 text-xs text-slate-500">
            Leave blank if you do not want a volatility cap.
          </p>
        </div>
      </div>

      <div className="mt-6 flex items-center gap-4">
        <button
          onClick={onSubmit}
          disabled={loading}
          className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-medium text-white shadow-[0_6px_18px_rgba(15,23,42,0.18)] transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
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
  let text = "The optimizer found a portfolio under the current constraints.";
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
   portfolio overview
========================================================= */

export function PortfolioOverview({ result }: { result: any }) {
  const desiredReturn = result.desired_return ?? result.target_return;
  const expectedReturn =
    result.expected_portfolio_return ?? result.portfolio_return;

  const cards = [
    {
      title: "Target return",
      value: pct(desiredReturn),
    },
    {
      title: "Expected return",
      value: pct(expectedReturn),
    },
    {
      title: "Volatility",
      value: pct(result.portfolio_volatility),
    },
    {
      title: "Largest weight",
      value: pct(result.largest_weight),
    },
    {
      title: "Positions",
      value:
        result.post_prune_assets ??
        result.active_positions ??
        "—",
    },
    {
      title: "Diversification ratio",
      value:
        result.diversification_ratio !== undefined &&
        result.diversification_ratio !== null
          ? result.diversification_ratio.toFixed(2)
          : "—",
    },
    {
      title: "Threshold used",
      value:
        result.concentration_threshold_used !== undefined &&
        result.concentration_threshold_used !== null
          ? `${(result.concentration_threshold_used * 100).toFixed(1)}%`
          : "—",
    },
    {
      title: "Recompute interval",
      value:
        typeof result.recompute_interval === "object"
          ? result.recompute_interval.interval_label
          : result.recompute_interval ?? result.recompute_schedule ?? "—",
    },
  ];

  return (
    <section className="rounded-[26px] border border-white/70 bg-white/88 p-4 shadow-[0_8px_28px_rgba(15,23,42,0.06)] backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
          Portfolio overview
        </h2>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-8">
        {cards.map((card) => (
          <div
            key={card.title}
            className="rounded-2xl border border-slate-200 bg-[linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] px-4 py-4"
          >
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
              {card.title}
            </p>
            <p className="mt-2 text-[28px] font-semibold tracking-tight text-slate-950">
              {card.value}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* =========================================================
   lightweight portfolio status note
========================================================= */

export function PortfolioStatusNote({
  universeStatus,
  marketData,
}: {
  universeStatus?: {
    effective_universe_count?: number;
    configured_count?: number;
    dropped_after_cleaning?: string[];
    final_missing_tickers?: string[];
    cache_warning?: string | null;
    refresh_summary?: string | null;
  };
  marketData?: {
    cache_status?: string;
    warning?: string | null;
  };
}) {
  const dropped = universeStatus?.dropped_after_cleaning || [];
  const missing = universeStatus?.final_missing_tickers || [];
  const warning = marketData?.warning || universeStatus?.cache_warning;

  const hasIssue = dropped.length > 0 || missing.length > 0 || !!warning;

  if (!hasIssue) return null;

  return (
    <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-wide">
        Portfolio status
      </p>

      {warning ? <p className="mt-2 text-sm">{warning}</p> : null}

      {typeof universeStatus?.effective_universe_count === "number" &&
      typeof universeStatus?.configured_count === "number" ? (
        <p className="mt-2 text-sm">
          Active universe: {universeStatus.effective_universe_count} of{" "}
          {universeStatus.configured_count} configured assets.
        </p>
      ) : null}

      {dropped.length > 0 ? (
        <p className="mt-2 text-sm">
          Dropped after cleaning: {dropped.join(", ")}.
        </p>
      ) : null}

      {missing.length > 0 ? (
        <p className="mt-2 text-sm">
          Still missing after recovery: {missing.join(", ")}.
        </p>
      ) : null}
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

export function AllocationChart({
  weights,
  tickerToName,
}: {
  weights: Record<string, number>;
  tickerToName?: Record<string, string>;
}) {
  const rows = Object.entries(weights)
    .filter(([_, v]) => v > 0.001)
    .sort((a, b) => b[1] - a[1]);

  const data = rows.map(([ticker, weight]) => ({
    name: ticker,
    value: Number((weight * 100).toFixed(2)),
  }));

  if (data.length === 0) return null;

  return (
    <Box
      title="Allocation"
      rightSlot={
        <span className="text-xs text-slate-400">{rows.length} positions</span>
      }
    >
      <div className="grid gap-4 lg:grid-cols-[180px_minmax(0,1fr)] lg:items-center">
        <div className="mx-auto h-[170px] w-[170px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                innerRadius={42}
                outerRadius={72}
                strokeWidth={1}
                labelLine={false}
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name) => [
                  `${Number(value).toFixed(2)}%`,
                  `${name} (${tickerToName?.[String(name)] || name})`,
                ]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="max-h-[190px] space-y-1 overflow-y-auto pr-1">
          {rows.map(([ticker, weight], i) => (
            <div
              key={ticker}
              className="grid grid-cols-[28px_minmax(0,1fr)_72px] items-center gap-2 rounded-2xl border border-slate-100 bg-slate-50/80 px-3 py-2.5"
            >
              <span className="text-xs font-medium text-slate-500">
                {i + 1}
              </span>

              <div className="flex min-w-0 items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                />
                <span className="truncate text-sm text-slate-800">
                  {ticker} ({tickerToName?.[ticker] || ticker})
                </span>
              </div>

              <span className="text-right text-sm font-semibold text-slate-900">
                {pct(weight)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Box>
  );
}

/* =========================================================
   category exposure chart
========================================================= */

export function CategoryExposureChart({
  categoryExposure,
}: {
  categoryExposure?: { category: string; weight: number; weight_percent?: number }[];
}) {
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

  const data = (categoryExposure || [])
    .map((item) => ({
      name: item.category,
      value:
        typeof item.weight_percent === "number"
          ? Number(item.weight_percent.toFixed(2))
          : Number((item.weight * 100).toFixed(2)),
    }))
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value);

  if (data.length === 0) return null;

  return (
    <Box
      title="Category exposure"
      rightSlot={
        <span className="text-xs text-slate-400">{data.length} categories</span>
      }
    >
      <div className="grid gap-4 lg:grid-cols-[180px_minmax(0,1fr)] lg:items-center">
        <div className="mx-auto h-[170px] w-[170px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                innerRadius={42}
                outerRadius={72}
                labelLine={false}
              >
                {data.map((_, index) => (
                  <Cell
                    key={index}
                    fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => {
                  const numericValue =
                    typeof value === "number"
                      ? value
                      : typeof value === "string"
                      ? Number(value)
                      : NaN;

                  return Number.isFinite(numericValue)
                    ? `${numericValue.toFixed(2)}%`
                    : "N/A";
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="max-h-[190px] space-y-1 overflow-y-auto pr-1">
          {data.map((item, index) => (
            <div
              key={item.name}
              className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2"
            >
              <div className="flex min-w-0 items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{
                    backgroundColor:
                      CATEGORY_COLORS[index % CATEGORY_COLORS.length],
                  }}
                />
                <span className="truncate text-sm text-slate-700">
                  {item.name}
                </span>
              </div>
              <span className="ml-3 text-sm font-semibold text-slate-900">
                {item.value.toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </Box>
  );
}

/* =========================================================
   backend-ranked top positions
========================================================= */

export function TopPositionsPanel({
  topPositions,
}: {
  topPositions?: {
    ticker: string;
    name?: string;
    category?: string;
    weight: number;
    weight_percent?: number;
  }[];
}) {
  const rows = (topPositions || []).filter((x) => x.weight > 0);

  if (rows.length === 0) return null;

  return (
    <Box
      title="Top positions"
      rightSlot={
        <span className="text-xs text-slate-400">backend-ranked</span>
      }
    >
      <div className="space-y-2">
        {rows.map((item, index) => (
          <div
            key={`${item.ticker}-${index}`}
            className="grid grid-cols-[28px_minmax(0,1fr)_90px] items-center gap-2 rounded-2xl border border-slate-100 bg-slate-50/80 px-3 py-3"
          >
            <span className="text-xs font-medium text-slate-500">
              {index + 1}
            </span>

            <div className="min-w-0">
              <div className="truncate text-sm font-medium text-slate-900">
                {item.ticker} ({item.name || item.ticker})
              </div>
              {item.category ? (
                <div className="mt-0.5 truncate text-xs text-slate-500">
                  {item.category}
                </div>
              ) : null}
            </div>

            <span className="text-right text-sm font-semibold text-slate-900">
              {typeof item.weight_percent === "number"
                ? `${item.weight_percent.toFixed(2)}%`
                : pct(item.weight)}
            </span>
          </div>
        ))}
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
  const filtered = (riskContributions || [])
    .filter((x) => x.value > 0.0001)
    .slice(0, 8);

  const total = filtered.reduce((sum, item) => sum + item.value, 0);

  const data =
    total > 0
      ? filtered
          .map((item) => ({
            name: item.ticker,
            value: Number(((item.value / total) * 100).toFixed(2)),
          }))
          .sort((a, b) => b.value - a.value)
      : [];

  if (data.length === 0) return null;

  return (
    <Box
      title="Risk contribution"
      rightSlot={
        <span className="text-xs text-slate-400">% of total contribution</span>
      }
    >
      <div className="h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 8, left: 0, bottom: 4 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              horizontal={false}
            />
            <XAxis
              type="number"
              tickFormatter={(value) => `${value}%`}
              domain={[0, "dataMax + 2"]}
              fontSize={11}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={48}
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              formatter={(value) => compactTooltipFormatter(value, "%", 2)}
            />
            <Bar dataKey="value" fill="#1d4ed8" radius={[0, 8, 8, 0]} />
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
        const rawX =
          item.bin ?? item.x ?? item.return ?? item.center ?? item.label ?? "";
        const rawY = item.count ?? item.frequency ?? item.y ?? item.value ?? 0;

        const xNumeric = typeof rawX === "number" ? rawX * 100 : Number(rawX);
        const xLabel =
          typeof rawX === "number"
            ? `${(rawX * 100).toFixed(1)}%`
            : String(rawX);

        return {
          x: xLabel,
          xNumeric: Number.isFinite(xNumeric) ? xNumeric : null,
          y: Number(rawY),
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
      xNumeric: typeof bin === "number" ? bin * 100 : Number(bin),
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
  const data = useMemo(
    () => normalizeSimulationChart(simulationChart),
    [simulationChart]
  );

  if (data.length === 0) return null;

  return (
    <Box title="Simulation distribution">
      <div className="h-[210px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 6, right: 8, left: 0, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e2e8f0"
              vertical={false}
            />
            <XAxis
              dataKey="x"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis fontSize={11} tickLine={false} axisLine={false} />
            <Tooltip
              formatter={(value) => compactTooltipFormatter(value, "", 0)}
              labelFormatter={(label) => `Return bucket: ${label}`}
            />
            <Area
              type="monotone"
              dataKey="y"
              stroke="#0f766e"
              fill="#99f6e4"
              fillOpacity={0.8}
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

  const cards = [
    { label: "Mean", value: pct(s?.mean_return ?? compact?.mean) },
    { label: "Median", value: pct(s?.median_return ?? compact?.median) },
    { label: "Loss prob.", value: pct(s?.loss_probability ?? compact?.loss_probability) },
    { label: "5th pct.", value: pct(s?.percentile_5 ?? compact?.p5) },
    { label: "95th pct.", value: pct(s?.percentile_95 ?? compact?.p95) },
  ];

  return (
    <Box title="Simulation summary">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {cards.map((item) => (
          <div
            key={item.label}
            className="rounded-2xl border border-slate-200 bg-[linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] px-4 py-4"
          >
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
              {item.label}
            </p>
            <p className="mt-2 text-lg font-semibold text-slate-950">
              {item.value}
            </p>
          </div>
        ))}
      </div>
    </Box>
  );
}

/* =========================================================
   weights table
========================================================= */

export function WeightsTable({
  weights,
  tickerToName,
}: {
  weights: Record<string, number>;
  tickerToName?: Record<string, string>;
}) {
  const rows = Object.entries(weights)
    .filter(([_, v]) => v > 0.001)
    .sort((a, b) => b[1] - a[1]);

  return (
    <Box
      title="Weights"
      rightSlot={
        <span className="text-xs text-slate-400">meaningful positions only</span>
      }
    >
      <div className="max-h-[280px] overflow-y-auto rounded-2xl border border-slate-200 bg-white">
        <div className="grid grid-cols-[44px_92px_minmax(0,1fr)_96px] border-b border-slate-200 bg-slate-50/80 px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
          <span>#</span>
          <span>Ticker</span>
          <span>Name</span>
          <span className="text-right">Weight</span>
        </div>

        <div className="divide-y divide-slate-100">
          {rows.map(([ticker, weight], index) => (
            <div
              key={ticker}
              className="grid grid-cols-[44px_92px_minmax(0,1fr)_96px] items-center px-4 py-3 text-sm"
            >
              <span className="text-slate-400">{index + 1}</span>
              <span className="font-semibold text-slate-950">{ticker}</span>
              <span className="truncate text-slate-600">
                {tickerName(ticker, tickerToName)}
              </span>
              <span className="text-right font-semibold text-slate-950">
                {pct(weight)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </Box>
  );
}

/* =========================================================
   explanation helpers
========================================================= */

function normalizeTextList(value: any): string[] {
  if (!value) return [];

  if (Array.isArray(value)) {
    return value.flatMap((item) => normalizeTextList(item)).filter(Boolean);
  }

  if (typeof value === "string") {
    return value
      .split(/\n{2,}/)
      .map((x) => x.trim())
      .filter(Boolean);
  }

  if (typeof value === "object") {
    return Object.values(value)
      .flatMap((item) => normalizeTextList(item))
      .filter(Boolean);
  }

  return [String(value)];
}

function normalizeVocabulary(rawVocabulary: any) {
  if (!rawVocabulary) return [];

  if (Array.isArray(rawVocabulary)) {
    return rawVocabulary.map((item: any, index: number) => {
      const text = String(item);
      const cleaned = text.replace(/^\d+:\s*/, "");
      const parts = cleaned.split("—");

      return {
        term: parts[0]?.trim() || `Term ${index + 1}`,
        definition: parts.slice(1).join("—").trim() || cleaned,
      };
    });
  }

  if (typeof rawVocabulary === "object") {
    return Object.entries(rawVocabulary).map(([key, value]) => ({
      term: String(key).replace(/^\d+:\s*/, "").trim(),
      definition: String(value),
    }));
  }

  return [];
}

function extractMetricChips(items: string[]) {
  if (!items.length) {
    return { chips: [], rest: [] as string[] };
  }

  const first = items[0] || "";

  const targetMatch = first.match(/Target return:\s*([\d.]+%)/i);
  const expectedMatch = first.match(/Expected return:\s*([\d.]+%)/i);
  const volMatch = first.match(/Volatility:\s*([\d.]+%)/i);

  const chips = [
    targetMatch ? { label: "Target", value: targetMatch[1] } : null,
    expectedMatch ? { label: "Expected", value: expectedMatch[1] } : null,
    volMatch ? { label: "Volatility", value: volMatch[1] } : null,
  ].filter(Boolean) as { label: string; value: string }[];

  const cleanedFirst = first
    .replace(/Target return:\s*[\d.]+%\.\s*/i, "")
    .replace(/Expected return:\s*[\d.]+%\.\s*/i, "")
    .replace(/Volatility:\s*[\d.]+%\.\s*/i, "")
    .replace(/\s{2,}/g, " ")
    .trim();

  const rest =
    cleanedFirst.length > 0 ? [cleanedFirst, ...items.slice(1)] : items.slice(1);

  return { chips, rest };
}

function TabButton({
  label,
  active,
  onClick,
  count,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  count?: number;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition",
        active
          ? "border-slate-900 bg-slate-900 text-white"
          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900",
      ].join(" ")}
    >
      <span>{label}</span>
      {typeof count === "number" && count > 0 ? (
        <span
          className={[
            "rounded-full px-2 py-0.5 text-xs",
            active ? "bg-white/20 text-white" : "bg-slate-100 text-slate-600",
          ].join(" ")}
        >
          {count}
        </span>
      ) : null}
    </button>
  );
}

function CommentaryCard({
  title,
  items,
  tone = "default",
}: {
  title: string;
  items: string[];
  tone?: "default" | "risk" | "simulation";
}) {
  if (!items.length) return null;

  const toneClass =
    tone === "risk"
      ? "border-blue-200 bg-blue-50"
      : tone === "simulation"
      ? "border-violet-200 bg-violet-50"
      : "border-slate-200 bg-white";

  return (
    <section className={`rounded-2xl border p-5 shadow-sm ${toneClass}`}>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-600">
        {title}
      </h3>

      <div className="mt-4 space-y-3">
        {items.map((item, i) => (
          <div
            key={i}
            className="rounded-xl bg-white/70 px-4 py-3 text-sm leading-7 text-slate-700"
          >
            {item}
          </div>
        ))}
      </div>
    </section>
  );
}

/* =========================================================
   explanation
========================================================= */

export function ExplanationSection({ explanation }: { explanation: any }) {
  const [activeTab, setActiveTab] = useState<
    "overview" | "risk" | "simulation" | "actions" | "vocabulary"
  >("overview");

  if (!explanation) return null;

  const portfolioSummary =
    typeof explanation === "string"
      ? normalizeTextList(explanation)
      : normalizeTextList(explanation?.portfolio_summary);

  const riskCommentary = normalizeTextList(explanation?.risk_commentary);
  const simulationCommentary = normalizeTextList(
    explanation?.simulation_commentary
  );

  const fallbackSummary =
    portfolioSummary.length === 0 &&
    riskCommentary.length === 0 &&
    simulationCommentary.length === 0
      ? [
          ...normalizeTextList(explanation?.summary),
          ...normalizeTextList(explanation?.text),
          ...normalizeTextList(explanation?.overview),
          ...normalizeTextList(explanation?.rationale),
          ...normalizeTextList(explanation?.portfolio_story),
        ]
      : [];

  const watch = normalizeTextList(explanation?.watch_for);
  const takeaways = normalizeTextList(explanation?.takeaways);
  const vocabularyEntries = normalizeVocabulary(explanation?.vocabulary);

  const mainSummary =
    portfolioSummary.length > 0
      ? portfolioSummary
      : fallbackSummary.length > 0
      ? fallbackSummary
      : [
          "Portfolio explanation generated from the current diagnostics and simulation output.",
        ];

  const { chips, rest: summaryBody } = useMemo(
    () => extractMetricChips(mainSummary),
    [mainSummary]
  );

  const tabCounts = {
    overview: summaryBody.length + chips.length,
    risk: riskCommentary.length,
    simulation: simulationCommentary.length,
    actions: Math.max(watch.length, 2) + takeaways.length,
    vocabulary: vocabularyEntries.length,
  };

  return (
    <section className="space-y-4">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Explanation</h2>
            <p className="mt-1 text-sm text-slate-500">
              Portfolio interpretation, risk context, scenario behavior, and action cues.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <TabButton
              label="Overview"
              active={activeTab === "overview"}
              onClick={() => setActiveTab("overview")}
              count={tabCounts.overview}
            />
            <TabButton
              label="Risk"
              active={activeTab === "risk"}
              onClick={() => setActiveTab("risk")}
              count={tabCounts.risk}
            />
            <TabButton
              label="Simulation"
              active={activeTab === "simulation"}
              onClick={() => setActiveTab("simulation")}
              count={tabCounts.simulation}
            />
            <TabButton
              label="Actions"
              active={activeTab === "actions"}
              onClick={() => setActiveTab("actions")}
              count={tabCounts.actions}
            />
            <TabButton
              label="Vocabulary"
              active={activeTab === "vocabulary"}
              onClick={() => setActiveTab("vocabulary")}
              count={tabCounts.vocabulary}
            />
          </div>
        </div>

        <div className="mt-5">
          {activeTab === "overview" && (
            <div className="space-y-4">
              {chips.length > 0 ? (
                <div className="grid gap-3 sm:grid-cols-3">
                  {chips.map((chip) => (
                    <div
                      key={chip.label}
                      className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4"
                    >
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                        {chip.label}
                      </p>
                      <p className="mt-2 text-xl font-semibold text-slate-900">
                        {chip.value}
                      </p>
                    </div>
                  ))}
                </div>
              ) : null}

              <div className="grid gap-3">
                {summaryBody.map((block, i) => (
                  <div
                    key={i}
                    className={[
                      "rounded-2xl border px-4 py-4 text-sm leading-7",
                      i === 0
                        ? "border-slate-200 bg-slate-50 font-medium text-slate-900"
                        : "border-slate-100 bg-white text-slate-700",
                    ].join(" ")}
                  >
                    {block}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "risk" && (
            <div>
              {riskCommentary.length > 0 ? (
                <CommentaryCard
                  title="Risk commentary"
                  items={riskCommentary}
                  tone="risk"
                />
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-500">
                  No risk commentary available.
                </div>
              )}
            </div>
          )}

          {activeTab === "simulation" && (
            <div>
              {simulationCommentary.length > 0 ? (
                <CommentaryCard
                  title="Simulation commentary"
                  items={simulationCommentary}
                  tone="simulation"
                />
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-500">
                  No simulation commentary available.
                </div>
              )}
            </div>
          )}

          {activeTab === "actions" && (
            <div className="grid gap-4 xl:grid-cols-2">
              <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 shadow-sm">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-800">
                  Watch for
                </h3>

                <div className="mt-3 space-y-3">
                  {watch.length > 0 ? (
                    watch.map((item, i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-amber-200 bg-white/75 px-4 py-3 text-sm leading-6 text-slate-700"
                      >
                        {item}
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="rounded-xl border border-amber-200 bg-white/75 px-4 py-3 text-sm leading-6 text-slate-700">
                        Monitor changes in the largest positions, as they can shift the portfolio’s risk profile.
                      </div>
                      <div className="rounded-xl border border-amber-200 bg-white/75 px-4 py-3 text-sm leading-6 text-slate-700">
                        Watch for increases in volatility or downside probability in the simulation results.
                      </div>
                    </>
                  )}
                </div>
              </section>

              <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 shadow-sm">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-emerald-800">
                  Takeaways
                </h3>

                {takeaways.length > 0 ? (
                  <div className="mt-3 space-y-3">
                    {takeaways.map((item, i) => (
                      <div
                        key={i}
                        className="rounded-xl border border-emerald-200 bg-white/75 px-4 py-3 text-sm leading-6 text-slate-700"
                      >
                        {item}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">
                    No takeaways available.
                  </p>
                )}
              </section>
            </div>
          )}

          {activeTab === "vocabulary" && (
            <div>
              {vocabularyEntries.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {vocabularyEntries.map((item: any, index: number) => (
                    <div
                      key={`${item.term}-${index}`}
                      className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 shadow-sm"
                    >
                      <p className="text-sm font-semibold text-slate-900">
                        {item.term}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-600">
                        {item.definition}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-500">
                  No vocabulary items available.
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    </section>
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
  prePruneAssets,
  postPruneAssets,
  concentrationThresholdUsed,
  concentrationCapped,
}: {
  concentration?: number;
  diversificationRatio?: number;
  meaningfulPositionsCount?: number;
  topRiskContributions: { ticker: string; value: number }[];
  prePruneAssets?: number;
  postPruneAssets?: number;
  concentrationThresholdUsed?: number;
  concentrationCapped?: boolean;
}) {
  const filtered = (topRiskContributions || []).filter((x) => x.value > 0);
  const total = filtered.reduce((sum, item) => sum + item.value, 0);

  const topRows =
    total > 0
      ? filtered.slice(0, 5).map((item) => ({
          ticker: item.ticker,
          value: Number(((item.value / total) * 100).toFixed(2)),
        }))
      : [];

  return (
    <Box title="Diagnostics">
      <div className="grid gap-3 lg:grid-cols-2 2xl:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Concentration
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-950">
            {num(concentration, 4)}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Diversification ratio
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-950">
            {num(diversificationRatio, 4)}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Positions
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-950">
            {meaningfulPositionsCount ?? "—"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Before concentration
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-950">
            {prePruneAssets ?? "—"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            After concentration
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-950">
            {postPruneAssets ?? meaningfulPositionsCount ?? "—"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Threshold used
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-950">
            {concentrationThresholdUsed !== undefined
              ? `${(concentrationThresholdUsed * 100).toFixed(1)}%`
              : "—"}
          </p>
          {concentrationCapped ? (
            <p className="mt-1 text-xs text-slate-500">20-asset cap applied</p>
          ) : null}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 lg:col-span-2 2xl:col-span-3">
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Top risk drivers
          </p>

          {topRows.length > 0 ? (
            <div className="mt-3 space-y-2">
              {topRows.map((item) => (
                <div
                  key={item.ticker}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-slate-700">{item.ticker}</span>
                  <span className="font-semibold text-slate-950">
                    {item.value.toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-500">
              No risk contribution data available.
            </p>
          )}
        </div>
      </div>
    </Box>
  );
}