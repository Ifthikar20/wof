"use client";

import type { ApiError } from "./types";

const CSRF_COOKIE = "wof_csrftoken";

function readCookie(name: string): string | null {
  const match = document.cookie.split("; ").find((c) => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

async function ensureCsrf(): Promise<string> {
  let token = readCookie(CSRF_COOKIE);
  if (!token) {
    await fetch("/api/v1/auth/csrf", { credentials: "same-origin" });
    token = readCookie(CSRF_COOKIE);
  }
  return token ?? "";
}

export class ApiException extends Error {
  constructor(public status: number, public body: ApiError | null) {
    super(body?.error?.message ?? `Request failed (${status})`);
  }
}

/** Same-origin JSON request with the session cookie and CSRF header. */
export async function api<T = unknown>(path: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
  const method = init.method ?? "GET";
  const headers: Record<string, string> = { Accept: "application/json" };
  if (method !== "GET") {
    headers["Content-Type"] = "application/json";
    headers["X-CSRFToken"] = await ensureCsrf();
  }
  const res = await fetch(`/api/v1${path}`, {
    method,
    headers,
    credentials: "same-origin",
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiException(res.status, data);
  return data as T;
}

export function fieldErrors(err: unknown): Record<string, string> {
  if (!(err instanceof ApiException) || !err.body?.error?.fields) return {};
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(err.body.error.fields)) {
    out[k] = Array.isArray(v) ? v.join(" ") : String(v);
  }
  return out;
}
