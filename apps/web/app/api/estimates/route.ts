import { proxyRequest } from "@/lib/proxy";

const estimatorBaseUrl = process.env.ESTIMATOR_API_BASE_URL ?? "http://127.0.0.1:8001";

export async function POST(request: Request) {
  return proxyRequest(request, new URL("/api/v1/estimates", estimatorBaseUrl));
}
