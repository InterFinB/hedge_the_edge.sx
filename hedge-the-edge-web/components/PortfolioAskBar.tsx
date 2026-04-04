"use client";

import { useMemo, useState } from "react";
import { askPortfolio } from "@/services/api";
import type {
  AIContext,
  AskPortfolioResponse,
  PortfolioConversationMessage,
} from "@/types/portfolio";

type PortfolioAskBarProps = {
  aiContext?: AIContext | null;
  disabled?: boolean;
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
}: PortfolioAskBarProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isOpen, setIsOpen] = useState(true);

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
    setIsOpen(true);

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
    <section className="rounded-[24px] border border-slate-200 bg-white/85 px-5 py-4 shadow-[0_10px_25px_rgba(15,23,42,0.04)] backdrop-blur">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-3 text-left"
      >
        <div>
          <div className="font-semibold text-slate-900">Ask Hedge The Edge</div>
          <p className="mt-1 text-sm text-slate-600">
            Ask follow-up questions about allocation, risk, simulation, and what to
            monitor next.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
            {hasContext ? "Connected to portfolio" : "AI context unavailable"}
          </div>
          <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
            {isOpen ? "Hide" : "Show"}
          </div>
        </div>
      </button>

      {isOpen && (
        <div className="mt-4">
          {!hasContext && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              The chat component is visible, but no AI context was returned from the
              backend portfolio response.
            </div>
          )}

          <div className="flex gap-2">
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
            <div className="mt-4 flex flex-wrap gap-2">
              {starterSuggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => void submitQuestion(suggestion)}
                  disabled={loading || disabled}
                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600 transition hover:border-slate-300 hover:bg-white hover:text-slate-900 disabled:opacity-60"
                >
                  {suggestion}
                </button>
              ))}
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
                    "rounded-[22px] px-4 py-4",
                    message.role === "user"
                      ? "ml-auto max-w-[85%] border border-slate-200 bg-slate-900 text-white"
                      : "max-w-[92%] border border-slate-200 bg-slate-50/80 text-slate-900",
                  ].join(" ")}
                >
                  {message.role === "assistant" ? (
                    <div className="space-y-4">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                        Hedge The Edge AI
                      </div>

                      <div className="space-y-4">
                        {splitIntoParagraphs(message.content).map((paragraph, index) => (
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
                        ))}
                      </div>

                      {message.why && message.why.length > 0 && (
                        <details className="pt-2">
                          <summary className="cursor-pointer text-xs text-slate-400 hover:text-slate-600">
                            Why this matters
                          </summary>
                          <div className="mt-3 space-y-2">
                            {message.why.map((item, i) => (
                              <div
                                key={i}
                                className="text-xs leading-6 text-slate-500"
                              >
                                • {item}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}

                      {message.followUps && message.followUps.length > 0 && (
                        <div className="flex flex-wrap gap-x-4 gap-y-2 pt-2">
                          {message.followUps.map((q, i) => (
                            <button
                              key={i}
                              type="button"
                              onClick={() => void submitQuestion(q)}
                              disabled={loading || disabled}
                              className="text-left text-xs text-slate-400 transition hover:text-slate-700 disabled:opacity-60"
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
                      <p className="text-sm leading-7 text-white">{message.content}</p>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="max-w-[92%] rounded-[22px] border border-slate-200 bg-slate-50/80 px-4 py-4 text-slate-900">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    Hedge The Edge AI
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
                    <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:150ms]" />
                    <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:300ms]" />
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