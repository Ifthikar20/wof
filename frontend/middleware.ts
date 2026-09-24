import { NextRequest, NextResponse } from "next/server";

/**
 * Per-request nonce-based Content-Security-Policy for HTML pages.
 * No 'unsafe-inline' scripts: even if sanitised story HTML were somehow bypassed,
 * injected <script> tags would not execute.
 */
export function middleware(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
  const isDev = process.env.NODE_ENV !== "production";
  const mediaHost = process.env.NEXT_PUBLIC_MEDIA_HOST ?? "";
  const secure = request.nextUrl.protocol === "https:" || request.headers.get("x-forwarded-proto") === "https";

  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' https://challenges.cloudflare.com${isDev ? " 'unsafe-eval'" : ""}`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' data: blob: ${mediaHost}`,
    `font-src 'self'`,
    `connect-src 'self' ${mediaHost}`,
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
    // HTML routes only: skip the API proxy, static assets and prefetches.
    {
      source: "/((?!api|_next/static|_next/image|favicon.ico|icon.svg).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
