import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Avatar } from "@/components/Avatar";
import { Comments } from "@/components/Comments";
import { ShareButton } from "@/components/ShareButton";
import { StoryActions } from "@/components/StoryActions";
import { StoryCard } from "@/components/StoryCard";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { artFor } from "@/lib/art";
import { serverGet } from "@/lib/server-api";
import type { Founder, Page, StoryCard as Card, StoryDetail } from "@/lib/types";

type Props = { params: Promise<{ slug: string }> };

async function load(slug: string) {
  if (!/^[a-z0-9-]{1,120}$/.test(slug)) return null;
  return serverGet<StoryDetail>(`/stories/${slug}`, { auth: true });
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const story = await load((await params).slug);
  if (!story) return {};
  return {
    title: story.title,
    description: story.dek,
    openGraph: { title: story.title, description: story.dek, type: "article", images: story.cover ? [story.cover.url] : [] },
  };
}

export default async function StoryPage({ params }: Props) {
  const story = await load((await params).slug);
  if (!story) notFound();
  const { author } = story;
  const [founder, more] = await Promise.all([
    serverGet<Founder>(`/founders/${author.handle}`),
    serverGet<Page<Card>>(`/stories?author=${author.handle}`),
  ]);
  const others = (more?.results ?? []).filter((s) => s.slug !== story.slug).slice(0, 4);
  const date = story.published_at ? new Date(story.published_at).toLocaleDateString("en", { dateStyle: "long" }) : "Unpublished draft";
  const name = author.display_name || author.handle;

  return (
    <article>
      {/* Full-frame header: the story's cover photo, or original artwork. */}
      <header className="relative -mx-4 overflow-hidden sm:mx-0 sm:rounded-[32px]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={story.cover?.url ?? artFor(story.slug)} alt="" className="absolute inset-0 h-full w-full object-cover"
             style={{ backgroundColor: story.cover?.dominant_color ?? "#2a2230" }} />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/35 to-black/10" />
        <div className="relative mx-auto flex min-h-[min(64vh,580px)] max-w-4xl flex-col justify-end gap-4 px-6 pb-10 pt-24 text-white sm:px-10">
          {story.status !== "published" && (
            <span className="w-fit rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[.14em] text-black">
              {story.status} · only visible to you
            </span>
          )}
          <div className="flex flex-wrap gap-2">
            {story.tags.map((t) => (
              <Link key={t} href={`/?tag=${t}`} className="glass rounded-full !bg-white/15 px-3 py-1 text-xs font-semibold capitalize text-white hover:!bg-white/25">
                {t.replace(/-/g, " ")}
              </Link>
            ))}
          </div>
          <h1 className="font-serif text-[clamp(2.5rem,6vw,5rem)] leading-[1] tracking-tight">{story.title}</h1>
          {story.dek && <p className="max-w-2xl text-lg text-white/80 sm:text-xl">{story.dek}</p>}
        </div>
      </header>

      <div className="mx-auto max-w-[680px]">
        {/* Byline + quick actions */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line py-6">
          <Link href={`/f/${author.handle}`} className="flex items-center gap-3">
            <Avatar name={name} size={44} />
            <span className="leading-tight">
              <span className="flex items-center gap-1.5 font-semibold">{name} {author.is_verified_founder && <VerifiedBadge />}</span>
              <span className="text-sm text-muted">
                {author.title && author.company ? `${author.title}, ${author.company} · ` : ""}{date} · {story.reading_minutes} min read
              </span>
            </span>
          </Link>
          <ShareButton title={story.title} />
        </div>

        {/* body_html is produced server-side: Markdown with raw HTML disabled, then an nh3
            allowlist sanitiser. The page CSP (nonce-only scripts) is the second barrier. */}
        <div className="prose-story drop-cap pt-4" dangerouslySetInnerHTML={{ __html: story.body_html }} />

        <StoryActions slug={story.slug} storyId={story.id} initialLiked={story.viewer?.liked ?? false} likeCount={story.like_count}
                      isAuthor={story.viewer?.is_author ?? false} status={story.status} />

        {/* About the author */}
        <section className="mt-10 flex gap-5 rounded-[24px] border border-line bg-surface/80 p-6">
          <Avatar name={name} size={56} />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-[.14em] text-muted">Written by</p>
            <Link href={`/f/${author.handle}`} className="mt-1 flex items-center gap-1.5 font-serif text-2xl">
              {name} {author.is_verified_founder && <VerifiedBadge className="h-5 w-5" />}
            </Link>
            {founder?.founder && (
              <p className="text-sm text-muted">
                {founder.founder.title} at {founder.founder.company} · verified via {founder.founder.domain}
              </p>
            )}
            {founder?.bio && <p className="mt-3">{founder.bio}</p>}
          </div>
        </section>

        {/* Integrity record */}
        <section className="mt-4 flex items-start gap-4 rounded-[24px] border border-line bg-surface/80 p-6 text-sm">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-chip" aria-hidden>
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M12 3 4 6v6c0 4.4 3.4 8.3 8 9 4.6-.7 8-4.6 8-9V6l-8-3Z" /><path d="m9 12 2 2 4-4" />
            </svg>
          </span>
          <div className="min-w-0">
            <p className="font-semibold">On the record · revision {story.revision_number}</p>
            <p className="mt-1 text-muted">Every edit is stored permanently and chained by hash. Anyone can check this text against its fingerprint:</p>
            <code className="mt-2 block break-all rounded-lg bg-chip px-2 py-1.5 font-mono text-[11px]">{story.content_hash}</code>
            {story.status === "published" && (
              <Link href={`/s/${story.slug}/history`} className="mt-3 inline-block font-semibold underline underline-offset-4">View the edit history</Link>
            )}
          </div>
        </section>

        {story.status === "published" && <Comments slug={story.slug} />}
      </div>

      {others.length > 0 && (
        <section className="mt-16">
          <h2 className="mb-5 font-serif text-3xl">More from {name}</h2>
          <div className="wall">{others.map((s) => <StoryCard key={s.slug} story={s} />)}</div>
        </section>
      )}
    </article>
  );
}
