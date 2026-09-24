"use client";

import { useEffect, useState } from "react";
import { Field } from "@/components/Field";
import { useMe } from "@/components/SessionProvider";
import { api, fieldErrors } from "@/lib/client-api";

export default function DataSettings() {
  const me = useMe();
  const [downloading, setDownloading] = useState(false);
  const [form, setForm] = useState({ password: "", otp: "", confirm: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (me === null) window.location.href = "/login?next=/settings/data";
  }, [me]);

  if (!me) return null;

  async function download() {
    setDownloading(true);
    try {
      const res = await fetch("/api/v1/auth/me/export", { credentials: "same-origin" });
      if (!res.ok) throw new Error(String(res.status));
      const blob = await res.blob();
      const name = /filename="([^"]+)"/.exec(res.headers.get("Content-Disposition") ?? "")?.[1] ?? "wall-of-founders-data.json";
      const url = URL.createObjectURL(blob);
      const a = Object.assign(document.createElement("a"), { href: url, download: name });
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-5xl leading-none">Your data</h1>
        <p className="mt-2 text-muted">Take a copy of everything, or delete your account.</p>
      </div>

      <section className="rounded-[24px] border border-line bg-surface/80 p-6">
        <h2 className="text-lg font-semibold">Download your data</h2>
        <p className="mt-1 max-w-xl text-sm text-muted">
          One JSON file with your profile, stories and every revision, comments, likes, boards, follows,
          verification requests, digest subscriptions and your account&apos;s security events.
        </p>
        <button className="btn btn-primary mt-5" onClick={download} disabled={downloading}>
          {downloading ? "Preparing…" : "Download my data"}
        </button>
      </section>

      <section className="rounded-[24px] border border-red-500/30 bg-red-500/5 p-6">
        <h2 className="text-lg font-semibold text-red-700">Delete account</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
          <li>Your stories come off the Wall; your comments are erased.</li>
          <li>Likes, boards, follows, digest subscriptions and uploads are deleted.</li>
          <li>Founder verification is revoked, and your handle can&apos;t be claimed by anyone else.</li>
          <li>Past revisions of removed stories stay in the tamper-evident record, linked to no one.</li>
        </ul>
        {!open ? (
          <button className="btn mt-5 bg-red-600 text-white hover:bg-red-700" onClick={() => setOpen(true)}>Delete my account…</button>
        ) : (
          <form
            className="mt-5 grid gap-4 sm:grid-cols-2"
            onSubmit={async (e) => {
              e.preventDefault();
              setErrors({});
              try {
                await api("/auth/me/delete", { method: "POST", body: form });
                window.location.href = "/";
              } catch (err) {
                setErrors(fieldErrors(err));
              }
            }}
          >
            <Field label="Password" error={errors.password}>
              <input id="delete-password" className="input" type="password" autoComplete="current-password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            </Field>
            {me.totp_enabled && (
              <Field label="Authenticator code" error={errors.otp}>
                <input id="delete-otp" className="input" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={form.otp} onChange={(e) => setForm({ ...form, otp: e.target.value })} />
              </Field>
            )}
            <Field label='Type "DELETE" to confirm' error={errors.confirm}>
              <input id="delete-confirm" className="input font-mono" required value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} />
            </Field>
            <div className="flex gap-2 sm:col-span-2">
              <button className="btn bg-red-600 text-white hover:bg-red-700" disabled={form.confirm !== "DELETE"}>Permanently delete my account</button>
              <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}
