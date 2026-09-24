import Link from "next/link";
import type { StoryCard as Story } from "@/lib/types";
import { VerifiedBadge } from "./VerifiedBadge";

const TINTS = ["--card-1", "--card-2", "--card-3", "--card-4", "--card-5", "--card-6"];

const HEIGHTS = [210, 250, 290, 330];

function hash(slug: string) {
  let h = 0;
  for (const ch of slug) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return h;
}

/** A pin on the wall. Stories without a cover become typographic cards so the wall
 *  still has Pinterest-like rhythm without needing an image for every story. */
export function StoryCard({ story }: { story: Story }) {
  const { cover, author } = story;
  const long = story.title.length > 48;
  const h = hash(story.slug);

  return (
    <article className="group">
      <Link href={`/s/${story.slug}`} className="block overflow-hidden rounded-2xl focus-visible:outline-2 focus-visible:outline-accent">
        {cover ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={cover.thumb_url}
            alt=""
            width={cover.width}
            height={cover.height}
            loading="lazy"
            style={{ backgroundColor: cover.dominant_color }}
            className="h-auto w-full transition duration-300 group-hover:brightness-90"
          />
        ) : (
          <div
            className="flex flex-col justify-between p-5 transition duration-300 group-hover:brightness-95"
            style={{ background: `var(${TINTS[h % TINTS.length]})`, minHeight: HEIGHTS[(h >> 3) % HEIGHTS.length] + (long ? 30 : 0) }}
          >
            <span className="text-[11px] font-semibold uppercase tracking-[.14em] text-muted">
              {story.tags[0]?.replace(/-/g, " ") ?? "Founder story"}
            </span>
            <h2 className={`font-serif font-bold leading-tight ${long ? "text-xl" : "text-2xl"}`}>{story.title}</h2>
            <span className="text-xs text-muted">{story.reading_minutes} min read</span>
          </div>
        )}
      </Link>
      <div className="px-1 pt-2">
        {cover && (
          <Link href={`/s/${story.slug}`} className="block font-semibold leading-snug hover:underline">
            {story.title}
          </Link>
        )}
        {story.dek && <p className="mt-0.5 line-clamp-2 text-sm text-muted">{story.dek}</p>}
        <Link href={`/f/${author.handle}`} className="mt-1.5 flex items-center gap-1.5 text-sm">
          <span className="grid h-6 w-6 place-items-center rounded-full bg-line text-[11px] font-bold">
            {(author.display_name || author.handle).slice(0, 1).toUpperCase()}
          </span>
          <span className="truncate font-medium">{author.display_name || author.handle}</span>
          {author.is_verified_founder && <VerifiedBadge />}
          {author.company && <span className="truncate text-muted">· {author.company}</span>}
        </Link>
      </div>
    </article>
  );
}
