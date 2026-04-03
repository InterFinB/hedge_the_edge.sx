"use client";

import type { AIContext } from "@/types/portfolio";

type PortfolioAskBarProps = {
  aiContext?: AIContext | null;
};

export default function PortfolioAskBar({
  aiContext,
}: PortfolioAskBarProps) {
  return (
    <section className="rounded-[24px] border border-blue-200 bg-blue-50/80 px-5 py-4 shadow-[0_10px_25px_rgba(15,23,42,0.04)]">
      <div className="font-semibold text-slate-900">Ask Hedge The Edge</div>
      <p className="mt-1 text-sm text-slate-700">
        Component loaded successfully.
      </p>
      <p className="mt-2 text-xs text-slate-500">
        AI context loaded: {aiContext ? "yes" : "no"}
      </p>
    </section>
  );
}