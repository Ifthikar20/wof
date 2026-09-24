"use client";

import QRCode from "qrcode";
import { useEffect, useState } from "react";
import { ChangePassword } from "@/components/ChangePassword";
import { useMe } from "@/components/SessionProvider";
import { api } from "@/lib/client-api";
import type { Me } from "@/lib/types";

/** TOTP setup. The QR code is drawn in the browser; the secret never goes to a third party. */
export default function SecuritySettings() {
  const me = useMe();
  const [enabled, setEnabled] = useState(false);
  const [uri, setUri] = useState("");
  const [qr, setQr] = useState("");
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (me === null) window.location.href = "/login?next=/settings/security";
    if (me) setEnabled(me.totp_enabled);
  }, [me]);

  useEffect(() => {
    if (uri) QRCode.toDataURL(uri, { margin: 1, width: 360, errorCorrectionLevel: "M" }).then(setQr).catch(() => setQr(""));
  }, [uri]);

  if (!me) return null;
  const secret = uri ? new URL(uri).searchParams.get("secret") ?? "" : "";
  const required = me.is_verified_founder || me.role !== "reader";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-5xl leading-none">Security</h1>
        <p className="mt-2 text-muted">Keep your account, and the stories published under your name, safe.</p>
      </div>

      <section className="rounded-[24px] border border-line bg-surface/80 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Two-factor authentication</h2>
            <p className="mt-1 max-w-md text-sm text-muted">
              A 6-digit code from an authenticator app at every login.
              {required ? " Required for founders and staff." : " Optional for readers, and recommended."}
            </p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${enabled ? "bg-emerald-600/10 text-emerald-700" : "bg-amber-500/15 text-amber-700"}`}>
            {enabled ? "On" : "Off"}
          </span>
        </div>

        {!enabled && !uri && (
          <button className="btn btn-primary mt-6 h-11 px-6"
                  onClick={async () => setUri((await api<{ otpauth_uri: string }>("/auth/2fa/setup", { method: "POST" })).otpauth_uri)}>
            Set up two-factor authentication
          </button>
        )}

        {!enabled && uri && (
          <form
            className="mt-6 grid gap-6 border-t border-line pt-6 sm:grid-cols-[180px_1fr]"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                const updated = await api<Me>("/auth/2fa/confirm", { method: "POST", body: { code } });
                setEnabled(updated.totp_enabled);
                setUri("");
              } catch (err) {
                setMsg(err instanceof Error ? err.message : "Invalid code.");
              }
            }}
          >
            <div className="rounded-2xl bg-white p-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {qr ? <img src={qr} alt="QR code for your authenticator app" className="h-auto w-full" /> : <div className="aspect-square" />}
            </div>
            <div className="flex flex-col gap-4">
              <div>
                <p className="text-sm font-semibold">1. Scan with your authenticator app</p>
                <p className="text-sm text-muted">Or enter this key manually (time-based):</p>
                <code className="mt-2 block select-all break-all rounded-lg bg-chip px-3 py-2 font-mono text-sm">{secret.replace(/(.{4})/g, "$1 ").trim()}</code>
              </div>
              <div>
                <label htmlFor="otp" className="text-sm font-semibold">2. Enter the 6-digit code it shows</label>
                <div className="mt-2 flex gap-2">
                  <input id="otp" className="input w-44 shrink-0 text-center font-mono tracking-[.35em]" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6}
                         required value={code} onChange={(e) => setCode(e.target.value)} placeholder="000000" />
                  <button className="btn btn-primary">Turn on</button>
                </div>
                {msg && <p className="mt-2 text-sm text-red-600" role="alert">{msg}</p>}
              </div>
            </div>
          </form>
        )}

        {enabled && <p className="mt-4 text-sm">You&apos;ll be asked for a code each time you log in. Each code works only once.</p>}
      </section>

      <ChangePassword />

      <section className="rounded-[24px] border border-line bg-surface/80 p-6 text-sm">
        <h2 className="text-lg font-semibold">How your account is protected</h2>
        <ul className="mt-3 grid gap-2 text-muted sm:grid-cols-2">
          <li>• Password stored with Argon2 (never readable, even by us)</li>
          <li>• Breached passwords are refused at sign-up</li>
          <li>• Login locks after repeated failed attempts</li>
          <li>• Session cookie that page scripts can&apos;t read</li>
          <li>• Suspended accounts are signed out everywhere</li>
          <li>• Every security event is written to a tamper-evident log</li>
        </ul>
      </section>
    </div>
  );
}
