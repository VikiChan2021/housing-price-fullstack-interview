import { NextResponse } from "next/server";

import { WEB_API_TIMEOUT_MS } from "./config";

const forwardedResponseHeaders = ["content-type", "content-disposition", "x-request-id"];

export async function proxyRequest(request: Request, target: URL): Promise<Response> {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  try {
    const upstream = await fetch(target, {
      method: request.method,
      body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
      headers: {
        "Content-Type": request.headers.get("content-type") ?? "application/json",
        "X-Request-ID": requestId,
      },
      cache: "no-store",
      signal: AbortSignal.timeout(WEB_API_TIMEOUT_MS),
    });
    const headers = new Headers();
    for (const name of forwardedResponseHeaders) {
      const value = upstream.headers.get(name);
      if (value) headers.set(name, value);
    }
    headers.set("X-Request-ID", upstream.headers.get("x-request-id") ?? requestId);
    return new Response(await upstream.arrayBuffer(), { status: upstream.status, headers });
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "UPSTREAM_UNAVAILABLE",
          message: "The requested service is temporarily unavailable. Please retry.",
          details: [],
          request_id: requestId,
        },
      },
      { status: 503, headers: { "X-Request-ID": requestId } },
    );
  }
}
