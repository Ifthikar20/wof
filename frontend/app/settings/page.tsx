"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Avatar } from "@/components/Avatar";
import { Field } from "@/components/Field";
import { useMe } from "@/components/SessionProvider";
import { api, fieldErrors } from "@/lib/client-api";
import type { Me } from "@/lib/types";

export default function ProfileSettings() {
  const me = useMe();
  const [form, setForm] = useState({ display_name: "", bio: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (me === null) window.location.href = "/login?next=/settings";
    if (me) setForm({ display_name: me.display_name, bio: me.bio ?? "" });
  }, [me]);

  if (!me) return null;

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    setSaved(false);
    try {
      await api<Me>("/auth/me", { method: "PATCH", body: form });
      setSaved(true);
    } catch (err) {
      setErrors(fieldErrors(err));
    }
  }

  return (
    <form onSubmit={save} className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-5xl leading-none">Profile</h1>
        <p className="mt-2 text-muted">How you appear on your stories, comments and profile page.</p>
      </div>

      <div className="flex items-center gap-4 rounded-[20px] border border-line bg-surface/80 p-5">
        <Avatar name={form.display_name || me.handle} size={64} />
        <div className="min-w-0">
          <p className="font-semibold">{form.display_name || me.handle}</p>
          <p className="text-sm text-muted">@{me.handle} · <Link href={`/f/${me.handle}`} className="underline underline-offset-4">View public profile</Link></p>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4 rounded-[20px] border border-line bg-surface/80 p-5">
        <div>
          <p className="font-semibold">Founder status</p>
          <p className="text-sm text-muted">
            {me.is_verified_founder ? "Verified founder. Your badge shows on everything you publish." : "Not verified yet. Verification lets you publish stories."}
          </p>
        </div>
        <Link href="/verify" className="btn btn-ghost">{me.is_verified_founder ? "Details" : "Get verified"}</Link>
      </div>

      <Field label="Display name" error={errors.display_name}>
        <input className="input" maxLength={80} value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
      </Field>
      <Field label="Bio" error={errors.bio} hint={`${form.bio.length}/280 · shown on your profile and under your stories`}>
        <textarea className="input min-h-28" maxLength={280} value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Email" hint="Private. Never shown on the site.">
          <input className="input opacity-70" value={me.email} readOnly />
        </Field>
        <Field label="Handle" hint="Your profile address. Handles can't be changed.">
          <input className="input opacity-70" value={`@${me.handle}`} readOnly />
        </Field>
      </div>
      <div className="flex items-center gap-3">
        <button className="btn btn-primary h-11 px-6">Save changes</button>
        {saved && <span className="text-sm text-emerald-700" role="status">Saved</span>}
      </div>
    </form>
  );
}
