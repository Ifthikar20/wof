"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AuthShell } from "@/components/AuthShell";
import { Field } from "@/components/Field";
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
    <AuthShell
      art={founder ? "/art/night.webp" : "/art/dusk-portrait.webp"}
      quote={founder ? "Your story, in your words, with your name verified." : "The founder stories worth keeping, all in one place."}
    >
      {/* Reader / founder switch: two paths into the same kind of account. */}
      <div role="tablist" aria-label="Account path" className="mb-8 grid grid-cols-2 rounded-full bg-chip p-1 text-sm font-semibold">
        {[false, true].map((f) => (
          <button key={String(f)} type="button" role="tab" aria-selected={founder === f} onClick={() => setFounder(f)}
                  className={`rounded-full py-2.5 transition ${founder === f ? "bg-surface shadow-sm" : "text-muted"}`}>
            {f ? "I'm a founder" : "Reader"}
          </button>
        ))}
      </div>
      <h1 className="font-serif text-5xl leading-none">{founder ? "Join as a founder" : "Join the Wall"}</h1>
      <p className="mb-6 mt-3 text-muted">
        {founder ? "Same account as everyone else. After this we verify you're a founder, then you can publish." : "Free. Save, like and comment on founder stories."}
      </p>
      {founder && (
        <ol className="mb-6 space-y-2 text-sm">
          {["Create your account", "Confirm an email on your company's domain", "Add LinkedIn or Crunchbase; a person reviews it", "Turn on 2FA, then publish"].map((step, i) => (
            <li key={step} className="flex items-center gap-3">
              <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-ink text-[11px] font-bold text-bg">{i + 1}</span>
              {step}
            </li>
          ))}
        </ol>
      )}
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Email" error={errors.email}><input className="input" type="email" autoComplete="email" required value={form.email} onChange={set("email")} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Handle" error={errors.handle}>
            <input className="input" required pattern="[a-z0-9_]{3,30}" placeholder="ada_l" value={form.handle} onChange={set("handle")} />
          </Field>
          <Field label="Display name" error={errors.display_name}><input className="input" maxLength={80} value={form.display_name} onChange={set("display_name")} /></Field>
        </div>
        <Field label="Password" error={errors.password || errors.non_field_errors} hint="12+ characters. Passwords found in data breaches are rejected.">
          <input className="input" type="password" autoComplete="new-password" minLength={12} required value={form.password} onChange={set("password")} />
        </Field>
        <Turnstile onToken={onToken} />
        {(errors.form || errors.turnstile_token) && <p className="text-sm text-red-600" role="alert">{errors.form || errors.turnstile_token}</p>}
        <button className="btn btn-primary mt-1 h-12 w-full text-[15px]" disabled={busy || done}>{busy ? "Creating…" : "Create account"}</button>
        <p className="mt-4 text-center text-sm text-muted">
          Already have an account?{" "}
          <Link className="font-semibold text-ink underline underline-offset-4" href={`/login?next=${encodeURIComponent(founder ? "/verify" : next)}`}>Log in</Link>
        </p>
      </form>
    </AuthShell>
  );
}
