import Link from "next/link";
import { Wall } from "@/components/Wall";
import { serverGet } from "@/lib/server-api";
import type { Page, StoryCard, Tag } from "@/lib/types";

export default async function Home({ searchParams }: { searchParams: Promise<{ tag?: string }> }) {
  const { tag } = await searchParams;
  const safeTag = tag && /^[a-z0-9-]{1,40}$/.test(tag) ? tag : undefined;
  const [page, tags] = await Promise.all([
    serverGet<Page<StoryCard>>(`/stories${safeTag ? `?tag=${safeTag}` : ""}`),
    serverGet<Tag[]>("/tags", { revalidate: 300 }),
  ]);

  return (
    <>
      <section className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="font-serif text-3xl font-bold tracking-tight md:text-4xl">Real stories from real founders.</h1>
          <p className="mt-1 text-muted">Every author is verified. Every edit is on the record.</p>
        </div>
        <Link href="/digest" className="btn btn-primary self-start md:self-auto">Get the weekly digest</Link>
      </section>

      <nav aria-label="Topics" className="-mx-4 mb-6 flex gap-2 overflow-x-auto px-4 pb-1">
        <Link href="/" className={`btn shrink-0 ${!safeTag ? "btn-primary" : "btn-ghost"}`}>All</Link>
        {(tags ?? []).map((t) => (
          <Link key={t.slug} href={`/?tag=${t.slug}`} className={`btn shrink-0 ${safeTag === t.slug ? "btn-primary" : "btn-ghost"}`}>
            {t.name}
          </Link>
        ))}
      </nav>

      <Wall key={safeTag ?? "all"} initial={page ?? { next: null, previous: null, results: [] }} />
    </>
  );
}
