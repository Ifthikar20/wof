"use client";

import Link from "next/link";
import { useState } from "react";
import { Card, Field } from "@/components/Field";
import { api, fieldErrors } from "@/lib/client-api";

export default function SignupPage() {
  const [form, setForm] = useState({ email: "", password: "", handle: "", display_name: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    try {
      await api("/auth/signup", { method: "POST", body: form });
      setDone(true);
      window.location.href = "/";
    } catch (err) {
      const fe = fieldErrors(err);
      setErrors(Object.keys(fe).length ? fe : { form: err instanceof Error ? err.message : "Signup failed." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Join the Wall" subtitle="Readers can save, like and comment. Founders can verify and publish.">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Email" error={errors.email}><input className="input" type="email" autoComplete="email" required value={form.email} onChange={set("email")} /></Field>
        <Field label="Handle" error={errors.handle} hint="3–30 lowercase letters, digits or underscores.">
          <input className="input" required pattern="[a-z0-9_]{3,30}" value={form.handle} onChange={set("handle")} />
        </Field>
        <Field label="Display name" error={errors.display_name}><input className="input" maxLength={80} value={form.display_name} onChange={set("display_name")} /></Field>
        <Field label="Password" error={errors.password || errors.non_field_errors} hint="At least 12 characters. Passwords found in data breaches are rejected.">
          <input className="input" type="password" autoComplete="new-password" minLength={12} required value={form.password} onChange={set("password")} />
        </Field>
        {errors.form && <p className="text-sm text-red-600" role="alert">{errors.form}</p>}
        <button className="btn btn-primary justify-center" disabled={busy || done}>{busy ? "Creating…" : "Create account"}</button>
        <p className="text-center text-sm text-muted">Already have an account? <Link className="underline" href="/login">Log in</Link></p>
      </form>
    </Card>
  );
}
