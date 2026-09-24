import "server-only";
import { cookies } from "next/headers";

const API = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";

/**
 * Server-side fetch to Django over the private network. Forwards the session cookie so
 * server-rendered pages can personalise (e.g. show drafts to their author).
 */
export async function serverGet<T>(path: string, opts: { auth?: boolean; revalidate?: number } = {}): Promise<T | null> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (opts.auth) {
    const jar = await cookies();
    const session = jar.get("wof_session") ?? jar.get("__Host-wof_session");
    if (session) headers.Cookie = `${session.name}=${session.value}`;
  }
  const res = await fetch(`${API}/api/v1${path}`, {
    headers,
    ...(opts.auth ? { cache: "no-store" as const } : { next: { revalidate: opts.revalidate ?? 30 } }),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return (await res.json()) as T;
}
