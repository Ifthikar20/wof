"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Field } from "@/components/Field";
import { useMe } from "@/components/SessionProvider";
import { api, ApiException, fieldErrors } from "@/lib/client-api";

type Req = { status: string; work_email: string; company_name: string; decision_reason: string };

const STATUS_COPY: Record<string, { title: string; body: string }> = {
  email_pending: { title: "Check your work inbox", body: "We sent a confirmation link to your work email. It's valid for 24 hours and works once." },
  under_review: { title: "A person is reviewing your evidence", body: "Your work email is confirmed. Reviews usually take up to 2 business days; we'll email you." },
  needs_info: { title: "We need a little more", body: "A moderator asked for more information. Update your details below and resubmit." },
  approved: { title: "You're verified", body: "Welcome to the Wall. Turn on 2FA, then publish your first story." },
  rejected: { title: "We couldn't verify this claim", body: "You can submit again with stronger evidence." },
};

/** Which of the 4 steps is done, current or upcoming, given the request state. */
function stepState(status: string | undefined, verified: boolean, totp: boolean) {
  const reached = verified ? (totp ? 4 : 3) : status === "under_review" || status === "needs_info" ? 2 : status === "email_pending" ? 1 : 1;
  return (i: number) => (i < reached ? "done" : i === reached ? "current" : "todo");
}

const STEPS = [
  { title: "Create your account", body: "Done. Same account as every reader." },
  { title: "Confirm a work email", body: "An address on your company's own domain. Personal mailboxes aren't accepted." },
  { title: "Evidence review", body: "A person checks your LinkedIn or Crunchbase against the company." },
  { title: "Turn on 2FA & publish", body: "Two-factor login keeps anyone else from publishing as you." },
];

export default function VerifyPage() {
  const me = useMe();
  const [current, setCurrent] = useState<Req | null | undefined>(undefined);
  const [form, setForm] = useState({ company_name: "", company_domain: "", work_email: "", role_title: "", linkedin_url: "", crunchbase_url: "", notes: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm({ ...form, [k]: e.target.value });

  useEffect(() => {
    api<Req | null>("/verification").then(setCurrent).catch((err) => {
      if (err instanceof ApiException && err.status === 403) window.location.href = "/login?next=/verify";
      setCurrent(null);
    });
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    setBusy(true);
    try {
      setCurrent(await api<Req>("/verification", { method: "POST", body: form }));
    } catch (err) {
      const fe = fieldErrors(err);
      setErrors(Object.keys(fe).length ? fe : { form: err instanceof Error ? err.message : "Failed." });
    } finally {
      setBusy(false);
    }
  }

  const verified = !!me?.is_verified_founder;
  const state = stepState(current?.status, verified, !!me?.totp_enabled);
  const showForm = !verified && current !== undefined && (!current || ["rejected", "needs_info"].includes(current.status));
  const copy = verified ? STATUS_COPY.approved : current ? STATUS_COPY[current.status] : undefined;

  return (
    <div className="mx-auto grid max-w-5xl gap-10 py-6 lg:grid-cols-[1fr_1.15fr]">
      <aside className="lg:sticky lg:top-24 lg:self-start">
        <p className="text-xs font-semibold uppercase tracking-[.16em] text-muted">Founder verification</p>
        <h1 className="mt-2 font-serif text-5xl leading-[1.02]">Prove it once. Publish with your name on it.</h1>
        <p className="mt-4 text-muted">Every founder on the Wall passes the same two checks. We never show your work email publicly.</p>
        <ol className="mt-8 flex flex-col gap-5">
          {STEPS.map((s, i) => {
            const st = state(i);
            return (
              <li key={s.title} className="flex gap-4">
                <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-bold ${
                  st === "done" ? "bg-ink text-bg" : st === "current" ? "border-2 border-ink" : "border border-line text-muted"}`}>
                  {st === "done" ? "✓" : i + 1}
                </span>
                <div className={st === "todo" ? "opacity-60" : ""}>
                  <p className="font-semibold">{s.title}</p>
                  <p className="text-sm text-muted">{s.body}</p>
                </div>
              </li>
            );
          })}
        </ol>
      </aside>

      <div className="flex flex-col gap-5">
        {copy && (
          <div className="rounded-[24px] border border-line bg-surface/80 p-6">
            {current && <p className="text-xs font-semibold uppercase tracking-[.14em] text-muted">{current.company_name} · {current.work_email}</p>}
            <p className="mt-2 font-serif text-3xl">{copy.title}</p>
            <p className="mt-1 text-muted">{copy.body}</p>
            {current?.decision_reason && <p className="mt-3 rounded-xl bg-chip px-3 py-2 text-sm">Moderator note: {current.decision_reason}</p>}
            {verified && (
              <Link href={me?.totp_enabled ? "/write" : "/settings/security"} className="btn btn-primary mt-5">
                {me?.totp_enabled ? "Write your first story" : "Turn on 2FA"}
              </Link>
            )}
          </div>
        )}

        {showForm && (
          <form onSubmit={submit} className="flex flex-col gap-4 rounded-[24px] border border-line bg-surface/80 p-6 sm:p-8">
            <h2 className="font-serif text-3xl">Your company</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Company name" error={errors.company_name}><input className="input" required placeholder="Acme" value={form.company_name} onChange={set("company_name")} /></Field>
              <Field label="Company domain" error={errors.company_domain}><input className="input" required placeholder="acme.com" value={form.company_domain} onChange={set("company_domain")} /></Field>
            </div>
            <Field label="Work email" error={errors.work_email} hint="Must be on your company domain. Gmail, Outlook and similar addresses aren't accepted.">
              <input className="input" type="email" required placeholder="you@acme.com" value={form.work_email} onChange={set("work_email")} />
            </Field>
            <Field label="Your role" error={errors.role_title}><input className="input" required placeholder="Co-founder & CEO" value={form.role_title} onChange={set("role_title")} /></Field>
            <h2 className="mt-4 font-serif text-3xl">Public evidence</h2>
            <p className="-mt-2 text-sm text-muted">At least one. A person opens these; we never fetch them automatically.</p>
            <Field label="LinkedIn profile" error={errors.linkedin_url}><input className="input" type="url" placeholder="https://www.linkedin.com/in/…" value={form.linkedin_url} onChange={set("linkedin_url")} /></Field>
            <Field label="Crunchbase page" error={errors.crunchbase_url}><input className="input" type="url" placeholder="https://www.crunchbase.com/organization/…" value={form.crunchbase_url} onChange={set("crunchbase_url")} /></Field>
            <Field label="Anything else for the reviewer?" error={errors.notes} hint="Encrypted, seen only by moderators, deleted after the decision.">
              <textarea className="input min-h-24" maxLength={2000} value={form.notes} onChange={set("notes")} />
            </Field>
            {errors.form && <p className="text-sm text-red-600" role="alert">{errors.form}</p>}
            <button className="btn btn-primary mt-2 h-12" disabled={busy}>{busy ? "Sending…" : "Send verification email"}</button>
          </form>
        )}
      </div>
    </div>
  );
}
