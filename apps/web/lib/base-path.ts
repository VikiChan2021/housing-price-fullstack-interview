// This public value is embedded at build time and must match the reverse-proxy mount path.
export const WEB_BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function withBasePath(path: string): string {
  // Normalize callers with or without a leading slash while preserving an empty local base path.
  return `${WEB_BASE_PATH}${path.startsWith("/") ? path : `/${path}`}`;
}
