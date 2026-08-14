function positiveSeconds(name: string, fallback: number): number {
  const parsed = Number.parseFloat(process.env[name] ?? "");
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export const WEB_API_TIMEOUT_MS = positiveSeconds("WEB_API_TIMEOUT_SECONDS", 10) * 1_000;
