"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/client-api";
import type { Me } from "@/lib/types";

export function HeaderActions() {
  const [me, setMe] = useState<Me | null | undefined>(undefined);

  useEffect(() => {
    api<Me | null>("/auth/me").then(setMe).catch(() => setMe(null));
  }, []);

  if (me === undefined) return <div className="h-9 w-40" />;

  if (!me) {
    return (
      <div className="flex items-center gap-2">
        <Link href="/login" className="btn btn-ghost">Log in</Link>
        <Link href="/signup" className="btn btn-primary">Sign up</Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {me.is_verified_founder ? (
        <Link href="/write" className="btn btn-primary">Write your story</Link>
      ) : (
        <Link href="/verify" className="btn btn-ghost">I&apos;m a founder</Link>
      )}
      <Link href="/boards" className="btn btn-ghost">Saved</Link>
      <Link href="/settings/security" className="btn btn-ghost hidden md:inline-flex">Security</Link>
      <button
        className="btn btn-ghost"
        onClick={async () => {
          await api("/auth/logout", { method: "POST" });
          window.location.href = "/";
        }}
      >
        Log out
      </button>
    </div>
  );
}
