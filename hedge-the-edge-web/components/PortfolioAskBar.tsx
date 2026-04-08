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
  return messages.map((m) => ({
    role: m.role,
    content: m.content,
  }));
}

function makeAssistantMessage(response: AskPortfolioResponse): ChatMessage {
  return {
    id: `assistant-${Date.now()}`,
    role: "assistant",
    content: response.answer,
    why: response.why ?? [],
    followUps: response.follow_ups ?? [],
  };
}

function splitIntoParagraphs(text: string): string[] {
  return text.split(/\n{2,}/).map((x) => x.trim()).filter(Boolean);
}

export default function PortfolioAskBar({
  aiContext,
  disabled = false,
  externalAsk = null,
}: PortfolioAskBarProps) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(true);

  const inputRef = useRef<HTMLInputElement | null>(null);

  const hasContext = !!aiContext;

  const starterSuggestions = [
    "What is the main risk in this portfolio?",
    "Why are the top positions weighted this way?",
    "How should I interpret the simulation results?",
    "What matters most before rebalancing?",
  ];

  const submitQuestion = useCallback(
    async (q?: string) => {
      const text = (q ?? question).trim();
      if (!text || !aiContext || loading) return;

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
      };

      const nextMessages = [...messages, userMessage];

      setMessages(nextMessages);
      setQuestion("");
      setLoading(true);

      try {
        const response = await askPortfolio({
          question: text,
          ai_context: aiContext,
          conversation: buildConversation(nextMessages),
        });

        setMessages([...nextMessages, makeAssistantMessage(response)]);
      } catch {
        setMessages([
          ...nextMessages,
          {
            id: "error",
            role: "assistant",
            content: "AI is temporarily unavailable.",
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [question, messages, aiContext, loading]
  );

  return (
    <section className="rounded-[28px] border border-slate-200 bg-gradient-to-b from-white to-slate-50 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.08)] backdrop-blur">
      
      {/* HEADER */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <h2 className="text-lg font-semibold text-slate-900">
              Hedge the Edge AI
            </h2>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Ask anything about your portfolio — risk, allocation, or scenarios.
          </p>
        </div>
      </div>

      {/* INPUT */}
      <div className="flex gap-2">
        <input
          ref={inputRef}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submitQuestion()}
          placeholder="Ask anything about your portfolio..."
          className="flex-1 rounded-2xl border border-slate-200 px-5 py-4 text-sm shadow-sm focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10 outline-none transition"
        />

        <button
          onClick={() => submitQuestion()}
          disabled={!question.trim() || loading}
          className="rounded-xl bg-slate-900 text-white px-6 py-3 font-semibold shadow-md hover:bg-slate-800 hover:shadow-lg transition disabled:opacity-50"
        >
          {loading ? "..." : "Ask"}
        </button>
      </div>

      {/* EMPTY STATE */}
      {!messages.length && (
        <div className="mt-4 text-sm text-slate-500">
          Start a conversation — I’ll help you break down this portfolio.
        </div>
      )}

      {/* SUGGESTIONS */}
      {!messages.length && (
        <div className="mt-4 flex flex-wrap gap-2">
          {starterSuggestions.map((s) => (
            <button
              key={s}
              onClick={() => submitQuestion(s)}
              className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600 hover:bg-white hover:shadow-md transition"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* CHAT */}
      <div className="mt-6 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={
              m.role === "user"
                ? "ml-auto max-w-[80%] bg-slate-900 text-white rounded-2xl px-4 py-3"
                : "max-w-[85%] bg-white border border-slate-200 rounded-2xl px-4 py-4 shadow-sm"
            }
          >
            {m.role === "assistant" ? (
              <div>
                <div className="text-xs text-slate-400 mb-2">
                  Hedge the Edge AI
                </div>

                {splitIntoParagraphs(m.content).map((p, i) => (
                  <p key={i} className="text-sm leading-7 text-slate-800">
                    {p}
                  </p>
                ))}
              </div>
            ) : (
              <p>{m.content}</p>
            )}
          </div>
        ))}

        {loading && (
          <div className="text-sm text-slate-500">Thinking...</div>
        )}
      </div>
    </section>
  );
}