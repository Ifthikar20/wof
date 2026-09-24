import type { Metadata } from "next";
import Link from "next/link";
import { SubscribeForm } from "@/components/SubscribeForm";
import { serverGet } from "@/lib/server-api";

export const metadata: Metadata = { title: "The Weekly Digest" };

type Issue = { number: number; subject: string; week_of: string };

export default async function DigestPage() {
  const issues = (await serverGet<Issue[]>("/digest/issues", { revalidate: 300 })) ?? [];
  return (
    <div>
      <section className="relative -mx-4 overflow-hidden sm:mx-0 sm:rounded-[32px]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/art/night.webp" alt="" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/35 to-transparent" />
        <div className="relative flex min-h-[min(64vh,560px)] max-w-2xl flex-col justify-end gap-4 p-6 text-white sm:p-12">
          <p className="text-xs font-semibold uppercase tracking-[.18em] text-white/70">The Weekly Digest</p>
          <h1 className="font-serif text-[clamp(2.6rem,5.5vw,4.75rem)] leading-[1]">The Reader&apos;s Digest for builders.</h1>
          <p className="text-lg text-white/80">
            Once a week: the founder stories people saved and talked about most, plus our editors&apos; picks.
            No ads, no tracking pixels, one-click unsubscribe.
          </p>
          <div className="mt-2 max-w-xl rounded-[22px] bg-white/95 p-2 text-ink"><SubscribeForm /></div>
        </div>
      </section>
      <div className="mx-auto max-w-2xl py-8">
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
    </div>
  );
}
