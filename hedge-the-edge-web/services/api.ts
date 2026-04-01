import type {
  AskPortfolioResponse,
  AIContext,
  PortfolioResponse,
} from "@/types/portfolio";

export async function generatePortfolio(payload: {
  target_return: number;
  max_volatility: number | null;
}): Promise<PortfolioResponse> {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!apiBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }

  const response = await fetch(`${apiBaseUrl}/portfolio`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const text = await response.text();

  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail =
      data &&
      typeof data === "object" &&
      "detail" in data &&
      typeof (data as { detail?: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : `Request failed with status ${response.status}`;

    throw new Error(detail);
  }

  if (!data || typeof data !== "object") {
    throw new Error("Backend returned an invalid response.");
  }

  return data as PortfolioResponse;
}

export async function askPortfolio(payload: {
  question: string;
  ai_context: AIContext;
  conversation?: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
}): Promise<AskPortfolioResponse> {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!apiBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }

  const response = await fetch(`${apiBaseUrl}/ask-portfolio`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const text = await response.text();

  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail =
      data &&
      typeof data === "object" &&
      "detail" in data &&
      typeof (data as { detail?: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : `Request failed with status ${response.status}`;

    throw new Error(detail);
  }

  if (!data || typeof data !== "object") {
    throw new Error("Backend returned an invalid AI response.");
  }

  return data as AskPortfolioResponse;
}