import type { PortfolioResponse } from "@/types/portfolio";

export async function generatePortfolio(payload: {
  target_return: number;
  max_volatility: number | null;
}): Promise<PortfolioResponse> {
  const response = await fetch("http://127.0.0.1:8000/portfolio", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || `Request failed with status ${response.status}`);
  }

  return data as PortfolioResponse;
}