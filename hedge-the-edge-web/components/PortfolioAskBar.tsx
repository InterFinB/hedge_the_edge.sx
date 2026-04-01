"use client";

import { FormEvent, useMemo, useState } from "react";
import { askPortfolio } from "@/services/api";
import type { AIContext, AskPortfolioResponse } from "@/types/portfolio";

type PortfolioAskBarProps = {
  aiContext?: AIContext | null;
};

const STARTER_QUESTIONS = [
  "Why is this portfolio concentrated?",
  "What is the main risk in this portfolio?",
  "What do the simulation results mean?",
  "Why are the top positions so large?",
];

function SectionList({
  title,
  items,
}: {
  title: string;
  items?: string[];
}) {
  if (!items || items.length === 0) return null;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
      <ul className="mt-3 space-y-2 text-sm text-gray-700">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="flex gap-2">
            <span className="mt-[2px] text-gray-400">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function PortfolioAskBar({
  aiContext,
}: PortfolioAskBarProps) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<AskPortfolioResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const disabled = !aiContext || loading;

  const placeholder = useMemo(() => {
    if (!aiContext) {
      return "Generate a portfolio first to ask Hedge The Edge.";
    }
    return "Ask Hedge The Edge about this portfolio...";
  }, [aiContext]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = question.trim();
    if (!trimmed || !aiContext) return;

    setLoading(true);
    setError("");

    try {
      const result = await askPortfolio({
        question: trimmed,
        ai_context: aiContext,
        conversation: [],
      });

      setResponse(result);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong while asking Hedge The Edge.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  function handleStarterQuestion(nextQuestion: string) {
    setQuestion(nextQuestion);
  }

  return (
    <section className="rounded-3xl border border-gray-200 bg-gray-50 p-5 shadow-sm">
      <div className="flex flex-col gap-2">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Ask Hedge The Edge
          </h3>
          <p className="text-sm text-gray-600">
            Ask a portfolio-specific question and get an explanation grounded in
            this portfolio’s actual weights, risks, and simulation results.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-2 flex flex-col gap-3">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            rows={3}
            className="w-full rounded-2xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-gray-500 disabled:cursor-not-allowed disabled:bg-gray-100"
          />

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="submit"
              disabled={disabled || !question.trim()}
              className="rounded-2xl bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {loading ? "Thinking..." : "Ask Hedge The Edge"}
            </button>

            {response ? (
              <span className="text-xs text-gray-500">
                Source: {response.source ?? "unknown"}
                {response.prompt_version
                  ? ` · Prompt: ${response.prompt_version}`
                  : ""}
              </span>
            ) : null}
          </div>
        </form>

        <div className="mt-2 flex flex-wrap gap-2">
          {STARTER_QUESTIONS.map((starter) => (
            <button
              key={starter}
              type="button"
              onClick={() => handleStarterQuestion(starter)}
              disabled={!aiContext || loading}
              className="rounded-full border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-700 transition hover:border-gray-400 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {starter}
            </button>
          ))}
        </div>

        {error ? (
          <div className="mt-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        {response ? (
          <div className="mt-4 space-y-4">
            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <h4 className="text-sm font-semibold text-gray-900">Answer</h4>
              <p className="mt-3 text-sm leading-6 text-gray-700">
                {response.answer}
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <SectionList
                title="Why Hedge The Edge says this"
                items={response.reasoning_summary}
              />
              <SectionList title="Watch for" items={response.watch_for} />
              <SectionList
                title="Good next questions"
                items={response.follow_up_suggestions}
              />
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}