import type { MarketInitialData } from "./types";
import { WEB_API_TIMEOUT_MS } from "./config";

const marketBaseUrl = process.env.MARKET_API_BASE_URL ?? "http://127.0.0.1:8080";

async function readJson<T>(path: string): Promise<T> {
  const response = await fetch(`${marketBaseUrl}${path}`, {
    cache: "no-store",
    headers: { "X-Request-ID": crypto.randomUUID() },
    signal: AbortSignal.timeout(WEB_API_TIMEOUT_MS),
  });
  if (!response.ok) {
    throw new Error(`Market API returned ${response.status} for ${path}`);
  }
  return (await response.json()) as T;
}

export async function getInitialMarketData(): Promise<MarketInitialData> {
  const [summary, properties] = await Promise.all([
    readJson<MarketInitialData["summary"]>("/api/v1/market/summary"),
    readJson<MarketInitialData["properties"]>("/api/v1/market/properties?page=0&size=10&sort=id,asc"),
  ]);
  return { summary, properties };
}
