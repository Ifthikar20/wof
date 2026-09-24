import Link from "next/link";
import { notFound } from "next/navigation";
import { SubscribeForm } from "@/components/SubscribeForm";
import { Wall } from "@/components/Wall";
import { serverGet } from "@/lib/server-api";
import type { StoryCard } from "@/lib/types";

type Issue = { number: number; subject: string; intro: string; week_of: string; stories: StoryCard[] };

export default async function IssuePage({ params }: { params: Promise<{ number: string }> }) {
  const { number } = await params;
  if (!/^\d{1,6}$/.test(number)) notFound();
  const issue = await serverGet<Issue>(`/digest/issues/${number}`, { revalidate: 3600 });
  if (!issue) notFound();
  const week = new Date(issue.week_of).toLocaleDateString("en", { dateStyle: "long" });
  return (
    <>
      <header className="relative -mx-4 overflow-hidden sm:mx-0 sm:rounded-[32px]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/art/night.webp" alt="" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/75 to-black/20" />
        <div className="relative flex min-h-[380px] flex-col items-center justify-end gap-3 px-6 pb-12 text-center text-white">
          <Link href="/digest" className="text-xs font-semibold uppercase tracking-[.18em] text-white/70 hover:text-white">The Weekly Digest · Issue #{issue.number}</Link>
          <h1 className="max-w-3xl font-serif text-[clamp(2.4rem,5vw,4.25rem)] leading-[1.02]">{issue.subject}</h1>
          <p className="text-sm text-white/70">Week of {week} · {issue.stories.length} stories</p>
        </div>
      </header>
      {issue.intro && <p className="mx-auto mt-10 max-w-2xl text-center font-serif text-2xl leading-snug">{issue.intro}</p>}
      <div className="mt-10"><Wall initial={{ next: null, previous: null, results: issue.stories }} /></div>
      <section className="mx-auto mt-16 max-w-xl rounded-[28px] border border-line bg-surface/80 p-8 text-center">
        <p className="font-serif text-3xl">Get the next issue</p>
        <p className="mb-5 mt-1 text-muted">One email a week. No tracking pixels.</p>
        <SubscribeForm />
      </section>
    </>
  );
}
