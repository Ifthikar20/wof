import type { MetadataRoute } from "next";
import { serverGet } from "@/lib/server-api";
import type { Page, StoryCard } from "@/lib/types";

export const dynamic = "force-dynamic";

// Only the latest page of stories: enough for search engines to discover new stories,
// without publishing a complete index of the corpus.
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = process.env.SITE_URL ?? "http://localhost:3000";
  const page = await serverGet<Page<StoryCard>>("/stories", { revalidate: 600 }).catch(() => null);
  return [
    { url: `${site}/`, changeFrequency: "hourly" },
    { url: `${site}/digest`, changeFrequency: "weekly" },
    ...(page?.results ?? []).map((s) => ({
      url: `${site}/s/${s.slug}`,
      lastModified: s.published_at ?? undefined,
    })),
  ];
}
