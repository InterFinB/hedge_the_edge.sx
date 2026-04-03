"use client";

import { useMemo, useState } from "react";
import { askPortfolio } from "@/services/api";
import type {
  AIContext,
  AskPortfolioResponse,
  ExplanationBlock,
  PortfolioConversationMessage,
} from "@/types/portfolio";

type PortfolioAskBarProps = {
  aiContext?: AIContext | null;
  explanation?: ExplanationBlock | null;
  disabled?: boolean;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta?: {
    reasoning_summary?: string[];
    watch_for?: string[];
    follow_up_suggestions?: string[];
  };
};

function normalizeExplanationSummary(
  explanation?: ExplanationBlock | null
): string {
  if (!explanation) return "";

  if (typeof explanation === "string") {
    return explanation;
  }

  const summary = explanation.portfolio_summary;

  if (Array.isArray(summary)) {
    return summary.join(" ");
  }

  if (typeof summary === "string") {
    return summary;
  }

  return "";
}

function buildConversation(
  messages: ChatMessage[]
): PortfolioConversationMessage[] {
  return messages.map((message) => ({
    role: message.role,
    content: message.content,
  }));
}

function makeAssistantMessage(response: AskPortfolioResponse): ChatMessage {
  return {
    id: `assistant-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role: "assistant",
    content: response.answer,
    meta: {
      reasoning_summary: response.reasoning_summary ?? [],
      watch_for: response.watch_for ?? [],
      follow_up_suggestions: response.follow_up_suggestions ?? [],
    },
  };
}

function getReadableAskError(error: unknown): string {
  if (!(error instanceof Error)) {
    return "Unable to get an AI response right now.";
  }

  const raw = error.message || "Unable to get an AI response right now.";
  const lower = raw.toLowerCase();

  if (
    lower.includes("not available") ||
    lower.includes("ask_portfolio_service") ||
    lower.includes("ai portfolio chat service")
  ) {
    return "AI chat is mounted, but the backend AI service is not available yet.";
  }

  if (lower.includes("500")) {
    return "The AI chat request reached the server, but the server could not complete it.";
  }

  return raw;
}

export default function PortfolioAskBar({
  aiContext,
  explanation,
  disabled = false,
}: PortfolioAskBarProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const hasContext = !!aiContext;

  const starterSuggestions = useMemo(
    () => [
      "What is the main risk in this portfolio?",
      "Why are the top positions weighted this way?",
      "How should I interpret the simulation results?",
      "What should I watch before rebalancing?",
    ],
    []
  );

  const explanationSummary = useMemo(
    () => normalizeExplanationSummary(explanation),
    [explanation]
  );

  const submitQuestion = async (rawQuestion?: string) => {
    const trimmed = (rawQuestion ?? question).trim();

    if (!trimmed || loading || disabled || !aiContext) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      role: "user",
      content: trimmed,
    };

    const nextMessages = [...messages, userMessage];

    setMessages(nextMessages);
    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const response = await askPortfolio({
        question: trimmed,
        ai_context: aiContext,
        conversation: buildConversation(nextMessages),
      });

      setMessages([...nextMessages, makeAssistantMessage(response)]);
    } catch (err) {
      setError(getReadableAskError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-[24px] border border-blue-200 bg-blue-50/80 px-5 py-4 shadow-[0_10px_25px_rgba(15,23,42,0.04)]">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="font-semibold text-slate-900">Ask Hedge The Edge</div>
          <p className="mt-1 text-sm text-slate-700">
            Ask follow-up questions about allocation, risk, simulation, and what to
            monitor next.
          </p>
        </div>

        <div className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
          AI context loaded: {hasContext ? "yes" : "no"}
        </div>
      </div>

      {!hasContext && (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          The chat component is visible, but no AI context was returned from the
          backend portfolio response.
        </div>
      )}

      {explanationSummary && (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-sm text-slate-700">
          <span className="font-semibold text-slate-900">Current context:</span>{" "}
          {explanationSummary}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              void submitQuestion();
            }
          }}
          disabled={!hasContext || loading || disabled}
          placeholder="Ask a question about this portfolio..."
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 disabled:cursor-not-allowed disabled:opacity-60"
        />
        <button
          type="button"
          onClick={() => void submitQuestion()}
          disabled={!hasContext || loading || disabled || !question.trim()}
          className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Asking..." : "Ask"}
        </button>
      </div>

      {!messages.length && hasContext && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Try one of these
          </p>
          <div className="flex flex-wrap gap-2">
            {starterSuggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => void submitQuestion(suggestion)}
                disabled={loading || disabled}
                className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 transition hover:border-slate-300 hover:text-slate-950 disabled:opacity-60"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {messages.length > 0 && (
        <div className="mt-5 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={[
                "rounded-2xl border px-4 py-4",
                message.role === "user"
                  ? "border-slate-200 bg-white"
                  : "border-blue-200 bg-white/90",
              ].join(" ")}
            >
              <div className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                {message.role === "user" ? "You" : "Hedge The Edge AI"}
              </div>

              <div className="text-sm leading-7 text-slate-800">
                {message.content}
              </div>

              {message.role === "assistant" && message.meta && (
                <div className="mt-4 space-y-3">
                  {message.meta.reasoning_summary?.length ? (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <div className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                        Reasoning summary
                      </div>
                      <div className="space-y-2">
                        {message.meta.reasoning_summary.map((item, index) => (
                          <div key={index} className="text-sm text-slate-700">
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {message.meta.watch_for?.length ? (
                    <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
                      <div className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-amber-800">
                        Watch for
                      </div>
                      <div className="space-y-2">
                        {message.meta.watch_for.map((item, index) => (
                          <div key={index} className="text-sm text-slate-700">
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {message.meta.follow_up_suggestions?.length ? (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
                      <div className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-800">
                        Follow-up ideas
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {message.meta.follow_up_suggestions.map((item, index) => (
                          <button
                            key={`${item}-${index}`}
                            type="button"
                            onClick={() => void submitQuestion(item)}
                            className="rounded-full border border-emerald-200 bg-white px-3 py-1.5 text-sm text-slate-700 transition hover:border-emerald-300 hover:text-slate-950"
                          >
                            {item}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}