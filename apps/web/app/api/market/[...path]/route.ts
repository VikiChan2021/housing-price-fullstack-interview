import { proxyRequest } from "@/lib/proxy";

const marketBaseUrl = process.env.MARKET_API_BASE_URL ?? "http://127.0.0.1:8080";

type Context = { params: Promise<{ path: string[] }> };

async function target(request: Request, context: Context) {
  // Next.js 16 exposes dynamic route params asynchronously, so await before rebuilding the path.
  const { path } = await context.params;
  const incoming = new URL(request.url);
  const upstream = new URL(`/api/v1/market/${path.join("/")}`, marketBaseUrl);
  // Preserve encoded filters and export options without parsing and reserializing their values.
  upstream.search = incoming.search;
  return upstream;
}

export async function GET(request: Request, context: Context) {
  return proxyRequest(request, await target(request, context));
}

export async function POST(request: Request, context: Context) {
  return proxyRequest(request, await target(request, context));
}
