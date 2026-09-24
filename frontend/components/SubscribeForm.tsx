"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/client-api";
import { Turnstile } from "./Turnstile";

export function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [token, setToken] = useState("");
  const onToken = useCallback((t: string) => setToken(t), []);

  return (
    <form
      className="flex flex-col gap-3 sm:flex-row sm:flex-wrap"
      onSubmit={async (e) => {
        e.preventDefault();
        try {
          const r = await api<{ message: string }>("/digest/subscribe", { method: "POST", body: { email, turnstile_token: token } });
          setMsg(r.message);
          setEmail("");
        } catch (err) {
          setMsg(err instanceof Error ? err.message : "Please try again.");
        }
      }}
    >
      <input className="input sm:flex-1" type="email" required placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      <button className="btn btn-primary justify-center">Subscribe</button>
      <div className="sm:basis-full"><Turnstile onToken={onToken} /></div>
      {msg && <p className="text-sm text-muted sm:basis-full" role="status">{msg}</p>}
    </form>
  );
}
