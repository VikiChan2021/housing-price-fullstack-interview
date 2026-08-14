import { NextResponse } from "next/server";

import { WEB_API_TIMEOUT_MS } from "@/lib/config";

const estimatorBaseUrl = process.env.ESTIMATOR_API_BASE_URL ?? "http://127.0.0.1:8001";
const marketBaseUrl = process.env.MARKET_API_BASE_URL ?? "http://127.0.0.1:8080";

async function ready(baseUrl: string) {
  try {
    const response = await fetch(new URL("/ready", baseUrl), {
      cache: "no-store",
      signal: AbortSignal.timeout(WEB_API_TIMEOUT_MS),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function GET() {
  const requestId = crypto.randomUUID();
  const [estimatorReady, marketReady] = await Promise.all([
    ready(estimatorBaseUrl),
    ready(marketBaseUrl),
  ]);
  if (!estimatorReady || !marketReady) {
    return NextResponse.json(
      {
        error: {
          code: "UPSTREAM_UNAVAILABLE",
          message: "One or more business services are not ready.",
          details: [
            { field: "estimator_api", message: estimatorReady ? "ready" : "not ready" },
            { field: "market_api", message: marketReady ? "ready" : "not ready" },
          ],
          request_id: requestId,
        },
      },
      { status: 503, headers: { "X-Request-ID": requestId } },
    );
  }
  return NextResponse.json({ status: "healthy", service: "web" }, { headers: { "X-Request-ID": requestId } });
}
