import Link from "next/link";
import type { StoryCard } from "@/lib/types";
import { VerifiedBadge } from "./VerifiedBadge";

/**
 * Full-frame hero: the editor's featured story over its cover photo, or over our own
 * artwork when the story has no cover. Text sits on a soft bottom gradient for contrast.
 */
export function Hero({ story }: { story: StoryCard }) {
  const image = story.cover?.url ?? "/art/dusk.webp";
  const { author } = story;

  return (
    <section className="relative -mx-4 mb-8 overflow-hidden sm:mx-0 sm:rounded-[32px]">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={image}
        alt=""
        className="absolute inset-0 h-full w-full object-cover"
        style={{ backgroundColor: story.cover?.dominant_color ?? "#3a2a33" }}
        fetchPriority="high"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/25 to-black/10" />

      <div className="relative flex min-h-[min(72vh,640px)] flex-col justify-end gap-5 p-6 text-white sm:p-10 lg:p-14">
        <span className="glass w-fit rounded-full !bg-white/15 px-3.5 py-1.5 text-xs font-semibold uppercase tracking-[.16em] text-white">
          Featured story
        </span>
        <Link href={`/s/${story.slug}`} className="max-w-4xl">
          <h1 className="font-serif text-[clamp(2.6rem,6vw,5.5rem)] leading-[0.98] tracking-tight">{story.title}</h1>
        </Link>
        {story.dek && <p className="max-w-2xl text-lg text-white/80 sm:text-xl">{story.dek}</p>}
        <div className="flex flex-wrap items-center gap-x-6 gap-y-4">
          <Link href={`/f/${author.handle}`} className="flex items-center gap-2.5">
            <span className="grid h-10 w-10 place-items-center rounded-full bg-white text-sm font-bold text-black">
              {(author.display_name || author.handle).slice(0, 1).toUpperCase()}
            </span>
            <span className="leading-tight">
              <span className="flex items-center gap-1.5 font-semibold">
                {author.display_name || author.handle}
                {author.is_verified_founder && <VerifiedBadge className="h-4 w-4" />}
              </span>
              {author.company && <span className="text-sm text-white/70">{author.title ? `${author.title}, ` : ""}{author.company}</span>}
            </span>
          </Link>
          <div className="flex gap-2">
            <Link href={`/s/${story.slug}`} className="btn bg-white text-black hover:bg-white/90">
              Read the story · {story.reading_minutes} min
            </Link>
            <Link href="/digest" className="btn glass !bg-white/15 text-white hover:!bg-white/25">
              Weekly digest
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
