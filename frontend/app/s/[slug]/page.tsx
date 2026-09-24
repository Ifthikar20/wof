import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { StoryActions } from "@/components/StoryActions";
import { Comments } from "@/components/Comments";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { serverGet } from "@/lib/server-api";
import type { StoryDetail } from "@/lib/types";

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
  const date = story.published_at ? new Date(story.published_at).toLocaleDateString("en", { dateStyle: "long" }) : "Draft";

  return (
    <article className="mx-auto max-w-2xl">
      {story.status !== "published" && (
        <p className="mb-4 rounded-xl border border-line bg-surface px-4 py-2 text-sm">
          This story is <strong>{story.status}</strong> and only visible to you.
        </p>
      )}
      <header className="mb-8">
        <div className="mb-3 flex flex-wrap gap-2">
          {story.tags.map((t) => (
            <Link key={t} href={`/?tag=${t}`} className="text-xs font-semibold uppercase tracking-[.14em] text-accent">
              {t.replace(/-/g, " ")}
            </Link>
          ))}
        </div>
        <h1 className="font-serif text-4xl leading-tight tracking-tight md:text-5xl">{story.title}</h1>
        {story.dek && <p className="mt-3 text-xl text-muted">{story.dek}</p>}
        <Link href={`/f/${author.handle}`} className="mt-6 flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-full bg-line font-bold">
            {(author.display_name || author.handle).slice(0, 1).toUpperCase()}
          </span>
          <span>
            <span className="flex items-center gap-1.5 font-semibold">
              {author.display_name || author.handle} {author.is_verified_founder && <VerifiedBadge />}
            </span>
            <span className="block text-sm text-muted">
              {author.title && author.company ? `${author.title}, ${author.company} · ` : ""}
              {date} · {story.reading_minutes} min read
            </span>
          </span>
        </Link>
      </header>

      {story.cover && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={story.cover.url} alt="" width={story.cover.width} height={story.cover.height}
             className="mb-8 h-auto w-full rounded-2xl" style={{ backgroundColor: story.cover.dominant_color }} />
      )}

      {/* body_html is produced server-side: Markdown with raw HTML disabled, then an nh3
          allowlist sanitiser. The page CSP (nonce-only scripts) is the second barrier. */}
      <div className="prose-story" dangerouslySetInnerHTML={{ __html: story.body_html }} />

      <StoryActions slug={story.slug} storyId={story.id} initialLiked={story.viewer?.liked ?? false} likeCount={story.like_count}
                    isAuthor={story.viewer?.is_author ?? false} status={story.status} />

      <details className="mt-6 rounded-xl border border-line bg-surface px-4 py-3 text-sm text-muted">
        <summary className="cursor-pointer font-medium text-ink">Integrity record</summary>
        <p className="mt-2">
          Revision {story.revision_number}. SHA-256 of this text:
        </p>
        <code className="mt-1 block break-all text-xs">{story.content_hash}</code>
        <p className="mt-2">
          Every revision is stored immutably and chained by hash.{" "}
          <a className="underline" href={`/api/v1/stories/${story.slug}/revisions`}>View the edit history</a>.
        </p>
      </details>

      {story.status === "published" && <Comments slug={story.slug} />}
    </article>
  );
}
