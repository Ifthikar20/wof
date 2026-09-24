"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiException } from "@/lib/client-api";
import type { Me } from "@/lib/types";

/** Email + password (+ TOTP step when the account has 2FA). Shared by /login and the auth prompt. */
export function LoginForm({ onSuccess, autoFocus = false }: { onSuccess: (me: Me) => void; autoFocus?: boolean }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [otp, setOtp] = useState("");
  const [needOtp, setNeedOtp] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      onSuccess(await api<Me>("/auth/login", { method: "POST", body: { email, password, otp } }));
    } catch (err) {
      if (err instanceof ApiException && err.body?.error.code === "otp_required") setNeedOtp(true);
      else setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3 text-left">
      <label className="sr-only" htmlFor="login-email">Email</label>
      <input id="login-email" className="input" type="email" autoComplete="email" placeholder="Email" required autoFocus={autoFocus}
             value={email} onChange={(e) => setEmail(e.target.value)} />
      <div className="relative">
        <label className="sr-only" htmlFor="login-password">Password</label>
        <input id="login-password" className="input pr-12" type={show ? "text" : "password"} autoComplete="current-password"
               placeholder="Password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="button" onClick={() => setShow(!show)} aria-label={show ? "Hide password" : "Show password"} aria-pressed={show}
                className="absolute right-2 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-full text-muted hover:bg-chip hover:text-ink">
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
            <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
            <circle cx="12" cy="12" r="3" />
            {show && <path d="M4 4l16 16" />}
          </svg>
        </button>
      </div>
      {needOtp && (
        <>
          <label className="sr-only" htmlFor="login-otp">Authenticator code</label>
          <input id="login-otp" className="input tracking-[.3em]" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}"
                 maxLength={6} placeholder="6-digit code" required autoFocus value={otp} onChange={(e) => setOtp(e.target.value)} />
          <p className="text-xs text-muted">Enter the code from your authenticator app.</p>
        </>
      )}
      <Link href="/forgot" className="-mt-1 w-fit text-sm font-semibold text-muted underline-offset-4 hover:text-ink hover:underline">
        Forgot password?
      </Link>
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      <button className="btn btn-primary mt-1 h-12 w-full text-[15px]" disabled={busy}>
        {busy ? "Logging in…" : "Log in"}
      </button>
    </form>
  );
}
