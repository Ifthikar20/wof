"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { AuthShell } from "@/components/AuthShell";
import { Field } from "@/components/Field";
import { Turnstile } from "@/components/Turnstile";
import { api } from "@/lib/client-api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [token, setToken] = useState("");
  const onToken = useCallback((t: string) => setToken(t), []);

  return (
    <AuthShell art="/art/night.webp" quote="Locked out happens to everyone. Let's get you back in.">
      {sent ? (
        <>
          <h1 className="font-serif text-5xl leading-none">Check your inbox</h1>
          <p className="mt-4 text-muted">
            If <strong className="text-ink">{email}</strong> has an account, we&apos;ve sent a link to choose a new password.
            It works once and expires in 1 hour.
          </p>
          <p className="mt-6 text-sm text-muted">Nothing after a few minutes? Check spam, or try again in 10 minutes.</p>
          <Link href="/login" className="btn btn-primary mt-8 h-12 w-full">Back to log in</Link>
        </>
      ) : (
        <form
          className="flex flex-col gap-4"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            try {
              await api("/auth/password/reset", { method: "POST", body: { email, turnstile_token: token } });
              setSent(true);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Please try again.");
            } finally {
              setBusy(false);
            }
          }}
        >
          <h1 className="font-serif text-5xl leading-none">Forgot your password?</h1>
          <p className="mb-4 text-muted">Enter the email you signed up with and we&apos;ll send a reset link.</p>
          <Field label="Email"><input className="input" type="email" autoComplete="email" required autoFocus value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
          <Turnstile onToken={onToken} />
          {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          <button className="btn btn-primary mt-1 h-12" disabled={busy}>{busy ? "Sending…" : "Send reset link"}</button>
          <p className="mt-4 text-center text-sm text-muted">
            Remembered it? <Link href="/login" className="font-semibold text-ink underline underline-offset-4">Log in</Link>
          </p>
        </form>
      )}
    </AuthShell>
  );
}
