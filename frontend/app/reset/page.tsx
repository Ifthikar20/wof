"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthShell } from "@/components/AuthShell";
import { Field } from "@/components/Field";
import { api, fieldErrors } from "@/lib/client-api";

export default function ResetPasswordPage() {
  const [link, setLink] = useState({ uid: "", token: "" });
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    setLink({ uid: q.get("uid") ?? "", token: q.get("token") ?? "" });
    // Remove the token from the address bar and history as soon as it's read.
    window.history.replaceState(null, "", "/reset");
  }, []);

  return (
    <AuthShell art="/art/dusk-portrait.webp" quote="A fresh start, with the same name on your stories.">
      {done ? (
        <>
          <h1 className="font-serif text-5xl leading-none">Password updated</h1>
          <p className="mt-4 text-muted">You&apos;ve been signed out everywhere else. Log in with your new password.</p>
          <Link href="/login" className="btn btn-primary mt-8 h-12 w-full">Log in</Link>
        </>
      ) : (
        <form
          className="flex flex-col gap-4"
          onSubmit={async (e) => {
            e.preventDefault();
            if (password !== confirm) return setErrors({ confirm: "The two passwords don't match." });
            setBusy(true);
            setErrors({});
            try {
              await api("/auth/password/reset/confirm", { method: "POST", body: { ...link, password } });
              setDone(true);
            } catch (err) {
              const fe = fieldErrors(err);
              setErrors(Object.keys(fe).length ? fe : { form: err instanceof Error ? err.message : "Please try again." });
            } finally {
              setBusy(false);
            }
          }}
        >
          <h1 className="font-serif text-5xl leading-none">Choose a new password</h1>
          <p className="mb-4 text-muted">At least 12 characters. Passwords found in data breaches are rejected.</p>
          <Field label="New password" error={errors.password}>
            <input className="input" type="password" autoComplete="new-password" minLength={12} required autoFocus value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          <Field label="Confirm new password" error={errors.confirm}>
            <input className="input" type="password" autoComplete="new-password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          </Field>
          {errors.form && (
            <p className="text-sm text-red-600" role="alert">
              {errors.form} <Link href="/forgot" className="underline">Request a new link</Link>
            </p>
          )}
          <button className="btn btn-primary mt-1 h-12" disabled={busy || !link.token}>{busy ? "Saving…" : "Save new password"}</button>
        </form>
      )}
    </AuthShell>
  );
}
