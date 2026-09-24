"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Card, Field } from "@/components/Field";
import { Turnstile } from "@/components/Turnstile";
import { api, fieldErrors } from "@/lib/client-api";
import { safeNext } from "@/lib/safe-redirect";

export default function SignupPage() {
  const [form, setForm] = useState({ email: "", password: "", handle: "", display_name: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState("");
  // Two paths, one account: founders create the same account, then go into verification.
  const [founder, setFounder] = useState(false);
  const [next, setNext] = useState("/");
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const isFounder = params.get("intent") === "founder";
    setFounder(isFounder);
    setNext(safeNext(params.get("next"), isFounder ? "/verify" : "/"));
  }, []);
  const onToken = useCallback((t: string) => setTurnstileToken(t), []);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    try {
      await api("/auth/signup", { method: "POST", body: { ...form, turnstile_token: turnstileToken } });
      setDone(true);
      window.location.href = founder ? "/verify" : next;
    } catch (err) {
      const fe = fieldErrors(err);
      setErrors(Object.keys(fe).length ? fe : { form: err instanceof Error ? err.message : "Signup failed." });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card
      title={founder ? "Join as a founder" : "Join the Wall"}
      subtitle={founder ? "Same account as everyone else. After this we verify you're a founder, then you can publish." : "Readers can save, like and comment. Founders get verified and publish."}
    >
      {founder && (
        <ol className="mb-5 list-decimal space-y-1 rounded-2xl bg-chip px-8 py-4 text-sm">
          <li>Create your account (this page)</li>
          <li>Confirm an email on your company&apos;s domain</li>
          <li>Add LinkedIn or Crunchbase; a person reviews it</li>
          <li>Turn on 2FA, then publish your story</li>
        </ol>
      )}
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Email" error={errors.email}><input className="input" type="email" autoComplete="email" required value={form.email} onChange={set("email")} /></Field>
        <Field label="Handle" error={errors.handle} hint="3–30 lowercase letters, digits or underscores.">
          <input className="input" required pattern="[a-z0-9_]{3,30}" value={form.handle} onChange={set("handle")} />
        </Field>
        <Field label="Display name" error={errors.display_name}><input className="input" maxLength={80} value={form.display_name} onChange={set("display_name")} /></Field>
        <Field label="Password" error={errors.password || errors.non_field_errors} hint="At least 12 characters. Passwords found in data breaches are rejected.">
          <input className="input" type="password" autoComplete="new-password" minLength={12} required value={form.password} onChange={set("password")} />
        </Field>
        <Turnstile onToken={onToken} />
        {(errors.form || errors.turnstile_token) && <p className="text-sm text-red-600" role="alert">{errors.form || errors.turnstile_token}</p>}
        <button className="btn btn-primary justify-center" disabled={busy || done}>{busy ? "Creating…" : "Create account"}</button>
        <p className="text-center text-sm text-muted">
          Already have an account? <Link className="underline" href={`/login?next=${encodeURIComponent(founder ? "/verify" : next)}`}>Log in</Link>
        </p>
        <button type="button" className="text-center text-sm font-semibold underline" onClick={() => setFounder(!founder)}>
          {founder ? "Just here to read? Join as a reader" : "Are you a founder? Join as a founder"}
        </button>
      </form>
    </Card>
  );
}
