import type { MetadataRoute } from "next";

// Search engines may index the HTML wall; nobody should crawl the JSON API, and bulk
// dataset/AI-training crawlers are refused outright. (Enforced for real at the edge;
// robots.txt is the polite, legally meaningful notice.)
export const dynamic = "force-dynamic"; // SITE_URL is read at runtime, not build time

export default function robots(): MetadataRoute.Robots {
  const site = process.env.SITE_URL ?? "http://localhost:3000";
  return {
    rules: [
      { userAgent: ["GPTBot", "CCBot", "ClaudeBot", "anthropic-ai", "Google-Extended", "Bytespider", "PerplexityBot", "Amazonbot"], disallow: "/" },
      { userAgent: "*", allow: "/", disallow: ["/api/", "/write", "/boards", "/verify", "/settings", "/digest/confirm", "/digest/unsubscribe"] },
    ],
    sitemap: `${site}/sitemap.xml`,
  };
}
