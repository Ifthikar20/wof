"use client";

import { useEffect, useState } from "react";
import { Card, Field } from "@/components/Field";
import { api } from "@/lib/client-api";
import type { Me } from "@/lib/types";

/** TOTP setup. The secret is shown for manual entry; nothing is sent to third-party QR services. */
export default function SecuritySettings() {
  const [me, setMe] = useState<Me | null>(null);
  const [uri, setUri] = useState("");
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api<Me | null>("/auth/me").then((m) => (m ? setMe(m) : (window.location.href = "/login?next=/settings/security")));
  }, []);

  const secret = uri ? new URL(uri).searchParams.get("secret") ?? "" : "";

  if (me?.totp_enabled) {
    return <Card title="Two-factor authentication"><p className="text-muted">2FA is on. You&apos;ll be asked for a code each time you log in.</p></Card>;
  }

  return (
    <Card title="Turn on two-factor authentication" subtitle="Required for founders before publishing. Use any authenticator app (1Password, Authy, Google Authenticator…).">
      {!uri ? (
        <button className="btn btn-primary" onClick={async () => setUri((await api<{ otpauth_uri: string }>("/auth/2fa/setup", { method: "POST" })).otpauth_uri)}>
          Generate my key
        </button>
      ) : (
        <form
          className="flex flex-col gap-4"
          onSubmit={async (e) => {
            e.preventDefault();
            try {
              setMe(await api<Me>("/auth/2fa/confirm", { method: "POST", body: { code } }));
            } catch (err) {
              setMsg(err instanceof Error ? err.message : "Invalid code.");
            }
          }}
        >
          <Field label="1. Add this key to your authenticator app" hint="Choose 'enter a setup key' and pick time-based.">
            <code className="input select-all break-all font-mono text-sm">{secret.replace(/(.{4})/g, "$1 ").trim()}</code>
          </Field>
          <Field label="2. Enter the 6-digit code it shows" error={msg}>
            <input className="input" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} required value={code} onChange={(e) => setCode(e.target.value)} />
          </Field>
          <button className="btn btn-primary justify-center">Turn on 2FA</button>
        </form>
      )}
    </Card>
  );
}
