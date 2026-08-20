import { NextResponse } from "next/server";

// Liveness checks only the Web process; dependency gating belongs to /api/ready.
export function GET() {
  return NextResponse.json({ status: "healthy", service: "web" });
}
