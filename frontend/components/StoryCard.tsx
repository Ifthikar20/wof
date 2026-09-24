import Link from "next/link";
import type { StoryCard as Story } from "@/lib/types";
import { SaveButton } from "./SaveButton";
import { VerifiedBadge } from "./VerifiedBadge";

const TINTS = ["--card-1", "--card-2", "--card-3", "--card-4", "--card-5", "--card-6"];
const HEIGHTS = [230, 290, 340, 390];

function hash(slug: string) {
  let h = 0;
  for (const ch of slug) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return h;
}

/**
 * A pin. Covers show as images; stories without a cover become typographic "posters"
 * (gradient + big serif title) so the wall stays image-first. Heights come from the slug
 * hash, which gives the masonry its staggered rhythm and keeps each card stable across visits.
 */
export function StoryCard({ story }: { story: Story }) {
  const { cover, author } = story;
  const h = hash(story.slug);
  const from = TINTS[h % TINTS.length];
  const to = TINTS[(h >>> 5) % TINTS.length];
  const topic = story.tags[0]?.replace(/-/g, " ");

  return (
    <article className="pin">
      <div className="pin-frame relative overflow-hidden rounded-[20px]">
        <Link href={`/s/${story.slug}`} aria-label={story.title} className="block focus-visible:outline-2 focus-visible:outline-accent">
          {cover ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={cover.thumb_url}
              alt=""
              width={cover.width}
              height={cover.height}
              loading="lazy"
              style={{ backgroundColor: cover.dominant_color }}
              className="block h-auto w-full"
            />
          ) : (
            <div
              className="flex flex-col items-center justify-center px-5 py-8 text-center"
              style={{
                background: `linear-gradient(160deg, var(${from}), var(${to === from ? TINTS[(h + 1) % TINTS.length] : to}))`,
                minHeight: HEIGHTS[(h >>> 3) % HEIGHTS.length],
              }}
            >
              <span aria-hidden className="font-serif text-6xl leading-none text-ink/20">“</span>
              <h2 className="font-serif text-[1.75rem] leading-[1.08] tracking-tight text-ink">{story.title}</h2>
            </div>
          )}
        </Link>

        {/* Hover overlay (hidden on touch devices via CSS). The container ignores clicks so
            they reach the card link; only the Save button captures them. */}
        <div className="pin-overlay pointer-events-none absolute inset-0 flex flex-col justify-between bg-black/40 p-3">
          <div className="flex items-start justify-between gap-2">
            <span className="truncate pt-2 text-sm font-semibold capitalize text-white">{topic ?? ""}</span>
            <SaveButton slug={story.slug} />
          </div>
          <div className="flex items-center justify-between">
            <span className="rounded-full bg-white/90 px-3 py-1.5 text-xs font-semibold text-black">{story.reading_minutes} min read</span>
            {story.save_count > 0 && <span className="rounded-full bg-white/90 px-3 py-1.5 text-xs font-semibold text-black">{story.save_count} saves</span>}
          </div>
        </div>
      </div>

      <div className="px-1.5 pt-2">
        {cover && (
          <Link href={`/s/${story.slug}`} className="line-clamp-2 text-[15px] font-semibold leading-snug">
            {story.title}
          </Link>
        )}
        <Link href={`/f/${author.handle}`} className="mt-1.5 flex min-w-0 items-center gap-1.5 text-[13px]">
          <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-ink text-[11px] font-bold text-bg">
            {(author.display_name || author.handle).slice(0, 1).toUpperCase()}
          </span>
          <span className="truncate">{author.display_name || author.handle}</span>
          {author.is_verified_founder && <VerifiedBadge className="h-3.5 w-3.5" />}
          {author.company && <span className="truncate text-muted">· {author.company}</span>}
        </Link>
      </div>
    </article>
  );
}
