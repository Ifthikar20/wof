import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Avatar } from "@/components/Avatar";
import { FollowButton } from "@/components/FollowButton";
import { ShareButton } from "@/components/ShareButton";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { Wall } from "@/components/Wall";
import { artFor } from "@/lib/art";
import { serverGet } from "@/lib/server-api";
import type { Founder, Page, StoryCard } from "@/lib/types";

type Props = { params: Promise<{ handle: string }> };
const valid = (h: string) => /^[a-z0-9_]{3,30}$/.test(h);

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { handle } = await params;
  return { title: valid(handle) ? `@${handle}` : "Founder" };
}

export default async function FounderPage({ params }: Props) {
  const { handle } = await params;
  if (!valid(handle)) notFound();
  const [founder, stories] = await Promise.all([
    serverGet<Founder>(`/founders/${handle}`),
    serverGet<Page<StoryCard>>(`/stories?author=${handle}`),
  ]);
  if (!founder) notFound();
  const name = founder.display_name || founder.handle;
  const count = stories?.results.length ?? 0;
  const since = founder.founder ? new Date(founder.founder.verified_at).toLocaleDateString("en", { month: "long", year: "numeric" }) : null;

  return (
    <>
      <section className="relative -mx-4 sm:mx-0">
        <div className="relative h-56 overflow-hidden sm:h-72 sm:rounded-[32px]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={artFor(founder.handle)} alt="" className="absolute inset-0 h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
        </div>
        <div className="relative mx-auto -mt-16 flex max-w-3xl flex-col items-center px-4 text-center">
          <Avatar name={name} size={128} className="border-[6px] border-bg text-5xl" />
          <h1 className="mt-4 flex items-center gap-2 font-serif text-5xl leading-none">
            {name} {founder.is_verified_founder && <VerifiedBadge className="h-7 w-7" />}
          </h1>
          <p className="mt-2 text-muted">@{founder.handle}</p>
          {founder.founder && (
            <p className="mt-4 rounded-full border border-line bg-surface/80 px-4 py-2 text-sm">
              {founder.founder.title} at <strong>{founder.founder.company}</strong>
              <span className="text-muted"> · verified via {founder.founder.domain}{since ? ` since ${since}` : ""}</span>
            </p>
          )}
          {founder.bio && <p className="mt-5 max-w-xl text-lg leading-relaxed">{founder.bio}</p>}
          <div className="mt-6 flex items-center gap-8 text-sm">
            <span><strong className="text-lg">{count}</strong> <span className="text-muted">{count === 1 ? "story" : "stories"}</span></span>
            <span><strong className="text-lg">{founder.follower_count}</strong> <span className="text-muted">followers</span></span>
          </div>
          <div className="mt-6 flex gap-2">
            {founder.is_verified_founder && <FollowButton handle={founder.handle} />}
            <ShareButton title={`${name} on Wall of Founders`} />
          </div>
        </div>
      </section>

      <div className="mx-auto mb-6 mt-12 flex max-w-3xl justify-center border-b border-line">
        <span className="border-b-2 border-ink px-4 pb-3 font-semibold">Stories</span>
      </div>
      <Wall initial={stories ?? { next: null, previous: null, results: [] }} emptyText={`${name} hasn't published a story yet.`} />
    </>
  );
}
