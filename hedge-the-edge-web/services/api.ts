import type {
  AskPortfolioRequest,
  AskPortfolioResponse,
  PortfolioResponse,
} from "@/types/portfolio";

function getApiBaseUrl() {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  if (!apiBaseUrl) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
  }

  return apiBaseUrl;
}

async function parseJsonResponse<T>(response: Response, fallbackError: string): Promise<T> {
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
        : fallbackError;

    throw new Error(detail);
  }

  if (!data || typeof data !== "object") {
    throw new Error("Backend returned an invalid response.");
  }

  return data as T;
}

export async function generatePortfolio(payload: {
  target_return: number;
  max_volatility: number | null;
}): Promise<PortfolioResponse> {
  const apiBaseUrl = getApiBaseUrl();

  const response = await fetch(`${apiBaseUrl}/portfolio`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<PortfolioResponse>(
    response,
    `Request failed with status ${response.status}`
  );
}

export async function askPortfolio(
  payload: AskPortfolioRequest
): Promise<AskPortfolioResponse> {
  const apiBaseUrl = getApiBaseUrl();

  const response = await fetch(`${apiBaseUrl}/ask-portfolio`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<AskPortfolioResponse>(
    response,
    `Request failed with status ${response.status}`
  );
}