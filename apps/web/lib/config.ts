function positiveSeconds(name: string, fallback: number): number {
  // Invalid environment text must fall back instead of disabling request timeouts with NaN.
  const parsed = Number.parseFloat(process.env[name] ?? "");
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

// AbortSignal.timeout expects milliseconds while operations configure human-friendly seconds.
export const WEB_API_TIMEOUT_MS = positiveSeconds("WEB_API_TIMEOUT_SECONDS", 10) * 1_000;
