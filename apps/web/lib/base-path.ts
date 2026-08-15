export const WEB_BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export function withBasePath(path: string): string {
  return `${WEB_BASE_PATH}${path.startsWith("/") ? path : `/${path}`}`;
}
