"use client";

import Link from "next/link";
import { useState } from "react";
import { Card, Field } from "@/components/Field";
import { api, ApiException } from "@/lib/client-api";
import { safeNext } from "@/lib/safe-redirect";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [needOtp, setNeedOtp] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/auth/login", { method: "POST", body: { email, password, otp } });
      const next = new URLSearchParams(window.location.search).get("next");
      window.location.href = safeNext(next);
    } catch (err) {
      if (err instanceof ApiException && err.body?.error.code === "otp_required") setNeedOtp(true);
      else setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Welcome back" subtitle="Log in to save, like and join the conversation.">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Field label="Email"><input className="input" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <Field label="Password"><input className="input" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        {needOtp && (
          <Field label="Authenticator code" hint="6 digits from your authenticator app.">
            <input className="input" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={otp} onChange={(e) => setOtp(e.target.value)} />
          </Field>
        )}
        {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
        <button className="btn btn-primary justify-center" disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
        <p className="text-center text-sm text-muted">New here? <Link className="underline" href="/signup">Create an account</Link></p>
      </form>
    </Card>
  );
}
