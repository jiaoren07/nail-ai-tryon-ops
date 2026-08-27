/** Mirror of api/client.ts baseURL fallback, for static asset paths. */
export const API_BASE: string =
  import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

/** Backend returns cover/result paths like `/static/covers/f_01.png`;
 * prefix them with the API origin unless already absolute. */
export function absUrl(path: string | null | undefined): string {
  if (!path) return "";
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}
