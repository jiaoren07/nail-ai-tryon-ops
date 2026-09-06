/** Single source of truth for the API origin (Batch G).
 *
 * - dev (`npm run dev`, port 5173): backend runs separately on :8000
 * - production build: the FastAPI backend serves the built frontend
 *   itself (single origin), so relative URLs ("") are correct
 * - VITE_API_BASE overrides both when a split deployment is wanted
 */
export const API_BASE: string =
  import.meta.env.VITE_API_BASE ??
  (import.meta.env.DEV ? "http://localhost:8000" : "");

/** Backend returns cover/result paths like `/static/covers/f_01.png`;
 * prefix them with the API origin unless already absolute. */
export function absUrl(path: string | null | undefined): string {
  if (!path) return "";
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}
