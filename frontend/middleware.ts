import { NextRequest, NextResponse } from "next/server";

// Django is reachable only on the private network. The browser talks to one origin, and
// /api/* (plus /local-media/* in no-Docker mode) is proxied here at request time, so the
// same image works in docker compose (http://backend:8000), ECS (http://api.wof.internal:8000)
// and local dev. (A next.config rewrite would bake the target in at build time.)
const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";

/**
 * 1. Proxy API and local-media requests to Django (runtime-configured).
 * 2. Per-request nonce-based Content-Security-Policy for HTML pages.
 *    No 'unsafe-inline' scripts: even if sanitised story HTML were somehow bypassed,
 *    injected <script> tags would not execute.
 */
export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  if (pathname.startsWith("/api/") || pathname.startsWith("/local-media/")) {
    return NextResponse.rewrite(new URL(pathname + search, API_INTERNAL_URL));
  }

  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const isDev = process.env.NODE_ENV !== "production";
  const mediaHost = process.env.NEXT_PUBLIC_MEDIA_HOST ?? "";
  const uploadHost = process.env.NEXT_PUBLIC_UPLOAD_HOST ?? ""; // presigned POST target (S3)
  const secure = request.nextUrl.protocol === "https:" || request.headers.get("x-forwarded-proto") === "https";

  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' https://challenges.cloudflare.com${isDev ? " 'unsafe-eval'" : ""}`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' data: blob: ${mediaHost}`,
    `font-src 'self'`,
    `connect-src 'self' ${mediaHost} ${uploadHost} https://challenges.cloudflare.com`,
    `frame-src https://challenges.cloudflare.com`,
    `object-src 'none'`,
    `base-uri 'none'`,
    `form-action 'self'`,
    `frame-ancestors 'none'`,
    secure ? "upgrade-insecure-requests" : "",
  ]
    .filter(Boolean)
    .join("; ");

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  return response;
}

export const config = {
  matcher: [
    "/api/:path*",
    "/local-media/:path*",
    // HTML routes: skip static assets and prefetches.
    {
      source: "/((?!api|local-media|_next/static|_next/image|favicon.ico|icon.svg).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
