"use client";

import { useEffect, useState } from "react";
import { Card, Field } from "@/components/Field";
import { api, ApiException, fieldErrors } from "@/lib/client-api";

type Req = { status: string; work_email: string; company_name: string; decision_reason: string };

const STATUS_COPY: Record<string, string> = {
  email_pending: "Check your work inbox: we sent a confirmation link (valid 24 hours).",
  under_review: "Email confirmed. A moderator is reviewing your evidence, usually within 2 business days.",
  needs_info: "A moderator needs more information. Update your details and resubmit.",
  approved: "You're verified. Welcome to the Wall!",
  rejected: "We couldn't verify this claim. You can submit again with more evidence.",
};

export default function VerifyPage() {
  const [current, setCurrent] = useState<Req | null | undefined>(undefined);
  const [form, setForm] = useState({ company_name: "", company_domain: "", work_email: "", role_title: "", linkedin_url: "", crunchbase_url: "", notes: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
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
    try {
      setCurrent(await api<Req>("/verification", { method: "POST", body: form }));
    } catch (err) {
      const fe = fieldErrors(err);
      setErrors(Object.keys(fe).length ? fe : { form: err instanceof Error ? err.message : "Failed." });
    }
  }

  const showForm = !current || ["rejected", "needs_info"].includes(current.status);

  return (
    <Card title="Verify you're a founder" subtitle="Two checks: an email on your company's domain, and public evidence a human reviews. We never publish your work email.">
      {current && (
        <div className="mb-6 rounded-xl border border-line p-4 text-sm">
          <p className="font-semibold">{current.company_name} · {current.work_email}</p>
          <p className="mt-1 text-muted">{STATUS_COPY[current.status] ?? current.status}</p>
          {current.decision_reason && <p className="mt-1">Moderator note: {current.decision_reason}</p>}
        </div>
      )}
      {showForm && current !== undefined && (
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Field label="Company name" error={errors.company_name}><input className="input" required value={form.company_name} onChange={set("company_name")} /></Field>
          <Field label="Company domain" error={errors.company_domain} hint="e.g. acme.com"><input className="input" required value={form.company_domain} onChange={set("company_domain")} /></Field>
          <Field label="Work email" error={errors.work_email} hint="Must be on your company domain. Gmail, Outlook and similar addresses are not accepted.">
            <input className="input" type="email" required value={form.work_email} onChange={set("work_email")} />
          </Field>
          <Field label="Your role" error={errors.role_title}><input className="input" required placeholder="Co-founder & CEO" value={form.role_title} onChange={set("role_title")} /></Field>
          <Field label="LinkedIn profile" error={errors.linkedin_url}><input className="input" type="url" placeholder="https://www.linkedin.com/in/…" value={form.linkedin_url} onChange={set("linkedin_url")} /></Field>
          <Field label="Crunchbase page" error={errors.crunchbase_url}><input className="input" type="url" placeholder="https://www.crunchbase.com/organization/…" value={form.crunchbase_url} onChange={set("crunchbase_url")} /></Field>
          <Field label="Anything else for the reviewer?" error={errors.notes} hint="Encrypted, seen only by moderators, and deleted after the decision.">
            <textarea className="input min-h-20" maxLength={2000} value={form.notes} onChange={set("notes")} />
          </Field>
          {errors.form && <p className="text-sm text-red-600" role="alert">{errors.form}</p>}
          <button className="btn btn-primary justify-center">Send verification email</button>
        </form>
      )}
    </Card>
  );
}
