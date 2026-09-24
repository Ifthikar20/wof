import type { Metadata } from "next";
import Link from "next/link";
import { SubscribeForm } from "@/components/SubscribeForm";
import { serverGet } from "@/lib/server-api";

export const metadata: Metadata = { title: "The Weekly Digest" };

type Issue = { number: number; subject: string; week_of: string };

export default async function DigestPage() {
  const issues = (await serverGet<Issue[]>("/digest/issues", { revalidate: 300 })) ?? [];
  return (
    <div className="mx-auto max-w-2xl py-8">
      <p className="text-xs font-semibold uppercase tracking-[.16em] text-accent">The Weekly Digest</p>
      <h1 className="mt-2 font-serif text-4xl font-bold leading-tight">The Reader&apos;s Digest for builders.</h1>
      <p className="mt-3 text-lg text-muted">
        Once a week: the founder stories people saved and talked about most, plus our editors&apos; picks. No ads and no tracking pixels. Unsubscribe in one click.
      </p>
      <div className="mt-8"><SubscribeForm /></div>
      {issues.length > 0 && (
        <section className="mt-14">
          <h2 className="mb-3 font-bold">Past issues</h2>
          <ul className="divide-y divide-line">
            {issues.map((i) => (
              <li key={i.number} className="py-3">
                <Link href={`/digest/${i.number}`} className="hover:underline">#{i.number} · {i.subject}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
