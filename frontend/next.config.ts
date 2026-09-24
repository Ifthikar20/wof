import type { NextConfig } from "next";

// Django is reachable only on the private network. The browser talks to one origin:
// /api/* is proxied to Django, so session cookies are first-party and no CORS is needed.
const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  output: "standalone",
  // Django's API routes have no trailing slash; don't let Next redirect them.
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_INTERNAL_URL}/api/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
          { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
