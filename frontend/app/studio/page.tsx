"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { FounderGate } from "@/components/FounderGate";
import { useMe } from "@/components/SessionProvider";
import { api } from "@/lib/client-api";
import { artFor } from "@/lib/art";
import type { Page, StoryDetail } from "@/lib/types";

const TABS = [
  { key: "all", label: "All" },
  { key: "draft", label: "Drafts" },
  { key: "published", label: "Published" },
  { key: "hidden", label: "Hidden" },
] as const;

const STATUS_STYLE: Record<string, string> = {
  draft: "bg-chip text-ink",
  published: "bg-emerald-600/10 text-emerald-700",
  hidden: "bg-amber-500/15 text-amber-700",
};

/** A founder's own stories: drafts, published and moderator-hidden, with quick actions. */
export default function StudioPage() {
  const me = useMe();
  const [stories, setStories] = useState<StoryDetail[] | null>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]["key"]>("all");

  const load = useCallback(() => {
    api<Page<StoryDetail>>("/me/stories").then((p) => setStories(p.results)).catch(() => setStories([]));
  }, []);

  useEffect(() => {
    if (me === null) window.location.href = "/login?next=/studio";
    else if (me) load();
  }, [me, load]);

  if (!me) return null;
  if (!me.is_verified_founder || !me.totp_enabled) return <FounderGate me={me} />;

  const all = stories ?? [];
  const shown = tab === "all" ? all : all.filter((s) => s.status === tab);
  const published = all.filter((s) => s.status === "published");
  const stats = [
    { label: "Published", value: published.length },
    { label: "Drafts", value: all.filter((s) => s.status === "draft").length },
    { label: "Likes", value: published.reduce((n, s) => n + s.like_count, 0) },
    { label: "Saves", value: published.reduce((n, s) => n + s.save_count, 0) },
  ];

  async function publish(slug: string) {
    await api(`/stories/${slug}/publish`, { method: "POST" });
    load();
  }

  async function remove(slug: string, title: string) {
    if (!window.confirm(`Remove “${title}”? It disappears from the wall; its revision history is kept.`)) return;
    await api(`/stories/${slug}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="mx-auto max-w-5xl py-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[.16em] text-muted">Studio</p>
          <h1 className="mt-2 font-serif text-5xl leading-none">Your stories</h1>
        </div>
        <Link href="/write" className="btn btn-primary h-12 px-6">+ New story</Link>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className="rounded-[20px] border border-line bg-surface/80 p-5">
            <p className="text-sm text-muted">{s.label}</p>
            <p className="mt-1 font-serif text-4xl">{s.value}</p>
          </div>
        ))}
      </div>

      <div role="tablist" className="mt-10 flex gap-2">
        {TABS.map((t) => (
          <button key={t.key} role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)} className={`chip ${tab === t.key ? "chip-active" : ""}`}>
            {t.label}
          </button>
        ))}
      </div>

      <ul className="mt-6 flex flex-col gap-3">
        {stories === null && <li className="py-12 text-center text-muted">Loading…</li>}
        {stories !== null && shown.length === 0 && (
          <li className="rounded-[24px] border border-dashed border-line py-16 text-center">
            <p className="font-serif text-3xl">Nothing here yet</p>
            <p className="mt-2 text-muted">Every founder has a story only they can tell.</p>
            <Link href="/write" className="btn btn-primary mt-6">Start writing</Link>
          </li>
        )}
        {shown.map((s) => (
          <li key={s.slug} className="flex items-center gap-4 rounded-[20px] border border-line bg-surface/80 p-3 pr-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={s.cover?.thumb_url ?? artFor(s.slug)} alt="" className="h-20 w-28 shrink-0 rounded-xl object-cover" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize ${STATUS_STYLE[s.status] ?? "bg-chip"}`}>{s.status}</span>
                <span className="text-xs text-muted">Rev {s.revision_number} · updated {new Date(s.updated_at).toLocaleDateString("en", { dateStyle: "medium" })}</span>
              </div>
              <Link href={`/s/${s.slug}`} className="mt-1 block truncate font-serif text-2xl leading-tight hover:underline">{s.title}</Link>
              {s.status === "published" && (
                <p className="text-xs text-muted">♥ {s.like_count} · {s.save_count} saves · {s.comment_count} comments</p>
              )}
              {s.status === "hidden" && <p className="text-xs text-amber-700">Hidden by a moderator. You can&apos;t edit it while it&apos;s under review.</p>}
            </div>
            <div className="flex shrink-0 flex-wrap justify-end gap-2">
              {s.status === "draft" && <button onClick={() => publish(s.slug)} className="btn btn-primary">Publish</button>}
              {s.status !== "hidden" && <Link href={`/write?slug=${s.slug}`} className="btn btn-ghost">Edit</Link>}
              {s.status !== "hidden" && (
                <button onClick={() => remove(s.slug, s.title)} aria-label={`Remove ${s.title}`} className="btn btn-ghost !px-3" title="Remove">
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" /></svg>
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
