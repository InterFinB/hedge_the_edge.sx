"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { askPortfolio } from "@/services/api";
import type {
  AIContext,
  AskPortfolioResponse,
  PortfolioConversationMessage,
  SelectionContext,
} from "@/types/portfolio";

type PortfolioAskBarProps = {
  aiContext?: AIContext | null;
  disabled?: boolean;
  externalAsk?: {
    nonce: number;
    question: string;
    selectionContext: SelectionContext | null;
    autoSubmit: boolean;
  } | null;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  why?: string[];
  followUps?: string[];
};

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
    why: response.why ?? [],
    followUps: response.follow_ups ?? [],
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

function splitIntoParagraphs(text: string): string[] {
  return text
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean);
}

export default function PortfolioAskBar({
  aiContext,
  disabled = false,
  externalAsk = null,
}: PortfolioAskBarProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isOpen, setIsOpen] = useState(true);
  const [pendingSelectionContext, setPendingSelectionContext] =
    useState<SelectionContext | null>(null);

  const inputRef = useRef<HTMLInputElement | null>(null);

  const hasContext = !!aiContext;

  const starterSuggestions = useMemo(
    () => [
      "What is the main risk in this portfolio?",
      "Why are the top positions weighted this way?",
      "How should I interpret the simulation results?",
      "What matters most before rebalancing?",
    ],
    []
  );

  const submitQuestion = useCallback(
    async (
      rawQuestion?: string,
      selectionOverride?: SelectionContext | null
    ) => {
      const trimmed = (rawQuestion ?? question).trim();

      if (!trimmed || loading || disabled || !aiContext) {
        return;
      }

      const activeSelectionContext =
        selectionOverride ?? pendingSelectionContext ?? null;

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
      setIsOpen(true);

      try {
        const response = await askPortfolio({
          question: trimmed,
          ai_context: {
            ...aiContext,
            selection_context: activeSelectionContext,
          },
          conversation: buildConversation(nextMessages),
        });

        setMessages([...nextMessages, makeAssistantMessage(response)]);
        setPendingSelectionContext(null);
      } catch (err) {
        setError(getReadableAskError(err));
      } finally {
        setLoading(false);
      }
    },
    [
      aiContext,
      disabled,
      loading,
      messages,
      pendingSelectionContext,
      question,
    ]
  );

  useEffect(() => {
    if (!externalAsk) return;

    setIsOpen(true);
    setError("");
    setPendingSelectionContext(externalAsk.selectionContext ?? null);
    setQuestion(externalAsk.question);

    window.setTimeout(() => {
      inputRef.current?.focus();
      inputRef.current?.select();
    }, 0);
  }, [externalAsk?.nonce, externalAsk]);

  return (
    <section className="overflow-hidden rounded-[28px] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.96)_0%,rgba(248,250,252,0.96)_100%)] px-5 py-5 shadow-[0_18px_48px_rgba(15,23,42,0.08)] backdrop-blur">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-start justify-between gap-4 text-left"
      >
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/60" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
            </span>
            <div className="text-lg font-semibold tracking-tight text-slate-950">
              Hedge the Edge AI
            </div>
          </div>

          <p className="mt-1.5 max-w-3xl text-sm leading-6 text-slate-600">
            Ask follow-up questions about allocation, risk, simulation, and what
            to monitor next.
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <div
            className={[
              "rounded-full border px-3 py-1.5 text-xs font-medium shadow-sm",
              hasContext
                ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                : "border-amber-200 bg-amber-50 text-amber-700",
            ].join(" ")}
          >
            {hasContext ? "Connected to portfolio" : "AI context unavailable"}
          </div>

          <div className="rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm">
            {isOpen ? "Hide" : "Show"}
          </div>
        </div>
      </button>

      {isOpen && (
        <div className="mt-5 border-t border-gradient-to-r from-transparent via-slate-200 to-transparent pt-5">
          {!hasContext && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 shadow-sm">
              The chat component is visible, but no AI context was returned from
              the backend portfolio response.
            </div>
          )}

          {pendingSelectionContext?.selected_text ? (
            <div className="mb-4 rounded-[22px] border border-slate-200 bg-white/80 px-4 py-4 text-sm text-slate-700 shadow-sm">
              <div className="mb-3 flex items-center justify-between gap-3">
                <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Reference text
                </div>
                <button
                  type="button"
                  onClick={() => setPendingSelectionContext(null)}
                  className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-500 transition hover:border-slate-300 hover:bg-white hover:text-slate-700"
                >
                  Clear
                </button>
              </div>
              <p className="line-clamp-4 leading-6 text-slate-700">
                “{pendingSelectionContext.selected_text}”
              </p>
            </div>
          ) : null}

          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-base text-slate-400">
                ✦
              </div>

              <input
                id="portfolio-ask-input"
                ref={inputRef}
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    void submitQuestion();
                  }
                }}
                disabled={!hasContext || loading || disabled}
                placeholder="Ask anything about your portfolio — risk, allocation, or scenarios…"
                className="w-full rounded-[22px] border border-slate-200 bg-white px-12 py-4 text-sm text-slate-900 shadow-[0_8px_24px_rgba(15,23,42,0.05)] outline-none transition placeholder:text-slate-400 focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 disabled:cursor-not-allowed disabled:opacity-60"
              />
            </div>

            <button
              type="button"
              onClick={() => void submitQuestion()}
              disabled={!hasContext || loading || disabled || !question.trim()}
              className="inline-flex items-center justify-center rounded-[20px] bg-slate-950 px-6 py-4 text-sm font-semibold text-white shadow-[0_12px_28px_rgba(15,23,42,0.18)] transition duration-200 hover:-translate-y-0.5 hover:bg-slate-900 hover:shadow-[0_16px_34px_rgba(15,23,42,0.22)] active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
            >
              {loading ? "Asking..." : "Ask AI"}
            </button>
          </div>

          {!messages.length && hasContext && (
            <div className="mt-4">
              <p className="mb-3 text-sm text-slate-500">
                Start a conversation — try one of these prompts.
              </p>

              <div className="flex flex-wrap gap-2.5">
                {starterSuggestions.map((suggestion, index) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => void submitQuestion(suggestion)}
                    disabled={loading || disabled}
                    className="rounded-full border border-slate-200 bg-slate-50/90 px-4 py-2.5 text-sm text-slate-600 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white hover:text-slate-900 hover:shadow-[0_8px_20px_rgba(15,23,42,0.08)] disabled:opacity-60"
                  >
                    <span className="mr-2 text-slate-400">
                      {index === 0
                        ? "⚠️"
                        : index === 1
                        ? "🧩"
                        : index === 2
                        ? "📊"
                        : "🔁"}
                    </span>
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 shadow-sm">
              {error}
            </div>
          )}

          {messages.length > 0 && (
            <div className="mt-6 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={[
                    "rounded-[24px] px-4 py-4 shadow-sm",
                    message.role === "user"
                      ? "ml-auto max-w-[85%] border border-slate-200 bg-slate-900 text-white shadow-[0_10px_28px_rgba(15,23,42,0.14)]"
                      : "max-w-[92%] border border-slate-200 bg-white/90 text-slate-900 shadow-[0_10px_28px_rgba(15,23,42,0.06)]",
                  ].join(" ")}
                  data-ask-section={
                    message.role === "assistant" ? "chat_response" : undefined
                  }
                  data-ask-label={
                    message.role === "assistant" ? "AI response" : undefined
                  }
                >
                  {message.role === "assistant" ? (
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        <span className="relative flex h-2 w-2">
                          <span className="absolute inline-flex h-full w-full animate-pulse rounded-full bg-violet-400/60" />
                          <span className="relative inline-flex h-2 w-2 rounded-full bg-violet-500" />
                        </span>
                        <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                          Hedge the Edge AI
                        </div>
                      </div>

                      <div className="space-y-4">
                        {splitIntoParagraphs(message.content).map(
                          (paragraph, index) => (
                            <p
                              key={index}
                              className={[
                                "leading-7",
                                index === 0
                                  ? "text-[16px] font-medium text-slate-950"
                                  : "text-[14px] text-slate-700",
                              ].join(" ")}
                            >
                              {paragraph}
                            </p>
                          )
                        )}
                      </div>

                      {message.why && message.why.length > 0 && (
                        <details className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3">
                          <summary className="cursor-pointer text-xs font-medium text-slate-500 transition hover:text-slate-700">
                            Why this matters
                          </summary>
                          <div className="mt-3 space-y-2">
                            {message.why.map((item, i) => (
                              <div
                                key={i}
                                className="text-xs leading-6 text-slate-600"
                              >
                                • {item}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}

                      {message.followUps && message.followUps.length > 0 && (
                        <div className="flex flex-wrap gap-2 pt-1">
                          {message.followUps.map((q, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => void submitQuestion(q)}
                              disabled={loading || disabled}
                              className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-left text-xs text-slate-500 transition hover:border-slate-300 hover:bg-white hover:text-slate-700 disabled:opacity-60"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-300">
                        You
                      </div>
                      <p className="text-sm leading-7 text-white">
                        {message.content}
                      </p>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="max-w-[92%] rounded-[24px] border border-slate-200 bg-white/90 px-4 py-4 text-slate-900 shadow-[0_10px_28px_rgba(15,23,42,0.06)]">
                  <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-pulse rounded-full bg-violet-400/60" />
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-violet-500" />
                    </span>
                    Hedge the Edge AI
                  </div>

                  <div className="mt-3 flex items-center gap-2">
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-slate-400" />
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-slate-400 [animation-delay:150ms]" />
                    <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-slate-400 [animation-delay:300ms]" />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}