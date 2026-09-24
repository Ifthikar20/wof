import Link from "next/link";
import { DigestPin } from "@/components/DigestPin";
import { Wall } from "@/components/Wall";
import { serverGet } from "@/lib/server-api";
import type { Page, StoryCard, Tag } from "@/lib/types";

type Props = { searchParams: Promise<{ tag?: string; q?: string }> };

export default async function Home({ searchParams }: Props) {
  const { tag, q } = await searchParams;
  const safeTag = tag && /^[a-z0-9-]{1,40}$/.test(tag) ? tag : undefined;
  const query = (q ?? "").trim().slice(0, 80) || undefined;

  const params = new URLSearchParams();
  if (safeTag) params.set("tag", safeTag);
  if (query) params.set("q", query);
  const qs = params.toString();

  const [page, tags] = await Promise.all([
    serverGet<Page<StoryCard>>(`/stories${qs ? `?${qs}` : ""}`),
    serverGet<Tag[]>("/tags", { revalidate: 300 }),
  ]);

  return (
    <>
      <nav aria-label="Topics" className="sticky top-16 z-10 -mx-4 mb-4 flex gap-2 overflow-x-auto bg-bg px-4 py-2">
        <Link href="/" className={`chip ${!safeTag && !query ? "chip-active" : ""}`}>All</Link>
        {(tags ?? []).map((t) => (
          <Link key={t.slug} href={`/?tag=${t.slug}`} className={`chip ${safeTag === t.slug ? "chip-active" : ""}`}>
            {t.name}
          </Link>
        ))}
      </nav>

      {query && (
        <h1 className="mb-4 text-center text-2xl font-semibold">
          Stories matching “{query}”
        </h1>
      )}

      <Wall
        key={qs || "all"}
        initial={page ?? { next: null, previous: null, results: [] }}
        promo={!qs ? <DigestPin /> : undefined}
        emptyText={query ? "No stories match that search yet." : undefined}
      />
    </>
  );
}
