"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const KEY = "wof.digestPin.dismissed";

/** A promoted "pin" inviting readers to the weekly digest. Dismissal is remembered per
 *  browser (a convenience only; storage may be unavailable, so it's wrapped). */
export function DigestPin() {
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    try {
      if (localStorage.getItem(KEY)) setHidden(true);
    } catch {
      /* storage blocked: just show the pin */
    }
  }, []);

  if (hidden) return null;

  return (
    <aside className="relative flex flex-col gap-3 rounded-2xl bg-ink p-6 text-bg" style={{ minHeight: 300 }}>
      <button
        aria-label="Dismiss"
        className="absolute right-3 top-3 grid h-8 w-8 place-items-center rounded-full text-bg/70 hover:bg-white/10"
        onClick={() => {
          setHidden(true);
          try {
            localStorage.setItem(KEY, "1");
          } catch {
            /* ignore */
          }
        }}
      >
        ✕
      </button>
      <span className="text-xs font-semibold uppercase tracking-[.16em] text-bg/60">The weekly digest</span>
      <p className="font-serif text-2xl font-bold leading-snug">The best founder stories, in your inbox every week.</p>
      <p className="text-sm text-bg/70">No ads. No tracking pixels. One-click unsubscribe.</p>
      <Link href="/digest" className="mt-auto self-start rounded-full bg-save px-4 py-2.5 text-sm font-bold text-white">
        Subscribe
      </Link>
    </aside>
  );
}
