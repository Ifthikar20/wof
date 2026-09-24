import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { serverGet } from "@/lib/server-api";
import type { StoryDetail } from "@/lib/types";

type Revision = { number: number; content_hash: string; chain_hash: string; created_at: string };
type Props = { params: Promise<{ slug: string }> };

export const metadata: Metadata = { title: "Edit history" };

/** Public, verifiable edit history: every revision's fingerprint, chained to the one before. */
export default async function HistoryPage({ params }: Props) {
  const { slug } = await params;
  if (!/^[a-z0-9-]{1,120}$/.test(slug)) notFound();
  const [story, revisions] = await Promise.all([
    serverGet<StoryDetail>(`/stories/${slug}`),
    serverGet<Revision[]>(`/stories/${slug}/revisions`),
  ]);
  if (!story || !revisions) notFound();
  const newestFirst = [...revisions].reverse();

  return (
    <div className="mx-auto max-w-3xl py-6">
      <Link href={`/s/${slug}`} className="text-sm font-semibold text-muted hover:text-ink">← Back to the story</Link>
      <p className="mt-8 text-xs font-semibold uppercase tracking-[.16em] text-muted">Edit history</p>
      <h1 className="mt-2 font-serif text-5xl leading-[1.02]">{story.title}</h1>
      <p className="mt-4 max-w-2xl text-muted">
        Every saved version of this story is kept permanently. Each one has a SHA-256 fingerprint of its text,
        chained to the version before it, so no version can be changed or removed without breaking the chain.
      </p>

      <ol className="relative mt-10 border-l border-line pl-8">
        {newestFirst.map((r, i) => (
          <li key={r.number} className="relative mb-8 last:mb-0">
            <span className={`absolute -left-[41px] top-1 grid h-5 w-5 place-items-center rounded-full border-2 ${i === 0 ? "border-ink bg-ink" : "border-line bg-bg"}`} aria-hidden />
            <div className="rounded-[20px] border border-line bg-surface/80 p-5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-semibold">
                  Revision {r.number} {i === 0 && <span className="ml-1 rounded-full bg-ink px-2 py-0.5 text-xs text-bg">current</span>}
                  {r.number === 1 && <span className="ml-1 rounded-full bg-chip px-2 py-0.5 text-xs">first draft</span>}
                </p>
                <time className="text-sm text-muted" dateTime={r.created_at}>
                  {new Date(r.created_at).toLocaleString("en", { dateStyle: "medium", timeStyle: "short" })}
                </time>
              </div>
              <dl className="mt-3 grid gap-2 text-xs">
                <div><dt className="text-muted">Text fingerprint</dt><dd className="break-all font-mono">{r.content_hash}</dd></div>
                <div><dt className="text-muted">Chain fingerprint</dt><dd className="break-all font-mono">{r.chain_hash}</dd></div>
              </dl>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
