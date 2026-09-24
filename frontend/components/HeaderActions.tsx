"use client";

import Link from "next/link";
import { api } from "@/lib/client-api";
import { useMe } from "./SessionProvider";

export function HeaderActions() {
  const me = useMe();

  if (me === undefined) return <div className="h-12 w-24 shrink-0" />;

  if (!me) {
    return (
      <div className="flex shrink-0 items-center gap-2">
        <Link href="/login" className="btn btn-primary">Log in</Link>
        <Link href="/signup" className="hidden rounded-full bg-chip px-4 py-2.5 text-[15px] font-semibold sm:inline-flex">Sign up</Link>
      </div>
    );
  }

  const initial = (me.display_name || me.handle).slice(0, 1).toUpperCase();

  return (
    <div className="flex shrink-0 items-center gap-2">
      {me.is_verified_founder ? (
        <Link href="/write" className="btn btn-primary">Write</Link>
      ) : (
        <Link href="/verify" className="hidden rounded-full bg-chip px-4 py-2.5 text-[15px] font-semibold sm:inline-flex">I&apos;m a founder</Link>
      )}
      {/* <details> gives an accessible, JS-free dropdown. */}
      <details className="relative">
        <summary
          aria-label="Account menu"
          className="grid h-12 w-12 cursor-pointer list-none place-items-center rounded-full hover:bg-chip [&::-webkit-details-marker]:hidden"
        >
          <span className="grid h-8 w-8 place-items-center rounded-full bg-ink text-sm font-bold text-bg">{initial}</span>
        </summary>
        <div className="absolute right-0 z-30 mt-2 w-56 rounded-2xl bg-surface p-2 shadow-[0_0_8px_rgba(0,0,0,.15)]">
          <p className="truncate px-3 py-2 text-xs text-muted">{me.email}</p>
          <Link href={`/f/${me.handle}`} className="block rounded-xl px-3 py-2 font-semibold hover:bg-chip">Your profile</Link>
          <Link href="/boards" className="block rounded-xl px-3 py-2 font-semibold hover:bg-chip">Saved</Link>
          <Link href="/settings/security" className="block rounded-xl px-3 py-2 font-semibold hover:bg-chip">Security</Link>
          <button
            className="block w-full rounded-xl px-3 py-2 text-left font-semibold hover:bg-chip"
            onClick={async () => {
              await api("/auth/logout", { method: "POST" });
              window.location.href = "/";
            }}
          >
            Log out
          </button>
        </div>
      </details>
    </div>
  );
}
