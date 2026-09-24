import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { FollowButton } from "@/components/FollowButton";
import { VerifiedBadge } from "@/components/VerifiedBadge";
import { Wall } from "@/components/Wall";
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

  return (
    <>
      <section className="mx-auto mb-10 flex max-w-2xl flex-col items-center text-center">
        <div className="grid h-24 w-24 place-items-center rounded-full bg-line text-3xl font-bold">
          {(founder.display_name || founder.handle).slice(0, 1).toUpperCase()}
        </div>
        <h1 className="mt-4 flex items-center gap-2 font-serif text-3xl font-bold">
          {founder.display_name || founder.handle} {founder.is_verified_founder && <VerifiedBadge className="h-6 w-6" />}
        </h1>
        <p className="text-muted">@{founder.handle}</p>
        {founder.founder && (
          <p className="mt-2">
            {founder.founder.title} at <strong>{founder.founder.company}</strong>
            <span className="text-muted"> · verified via {founder.founder.domain}</span>
          </p>
        )}
        {founder.bio && <p className="mt-3 max-w-lg">{founder.bio}</p>}
        <div className="mt-4 flex items-center gap-3">
          <span className="text-sm text-muted">{founder.follower_count} followers</span>
          {founder.is_verified_founder && <FollowButton handle={founder.handle} />}
        </div>
      </section>
      <Wall initial={stories ?? { next: null, previous: null, results: [] }} />
    </>
  );
}
