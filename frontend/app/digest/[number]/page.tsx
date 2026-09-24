import { notFound } from "next/navigation";
import { Wall } from "@/components/Wall";
import { serverGet } from "@/lib/server-api";
import type { StoryCard } from "@/lib/types";

type Issue = { number: number; subject: string; intro: string; week_of: string; stories: StoryCard[] };

export default async function IssuePage({ params }: { params: Promise<{ number: string }> }) {
  const { number } = await params;
  if (!/^\d{1,6}$/.test(number)) notFound();
  const issue = await serverGet<Issue>(`/digest/issues/${number}`, { revalidate: 3600 });
  if (!issue) notFound();
  return (
    <>
      <header className="mx-auto mb-8 max-w-2xl text-center">
        <p className="text-xs font-semibold uppercase tracking-[.16em] text-accent">Issue #{issue.number} · week of {issue.week_of}</p>
        <h1 className="mt-2 font-serif text-3xl">{issue.subject}</h1>
        {issue.intro && <p className="mt-3 text-muted">{issue.intro}</p>}
      </header>
      <Wall initial={{ next: null, previous: null, results: issue.stories }} />
    </>
  );
}
