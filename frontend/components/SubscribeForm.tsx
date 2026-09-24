"use client";

import { useState } from "react";
import { api } from "@/lib/client-api";

export function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");

  return (
    <form
      className="flex flex-col gap-3 sm:flex-row"
      onSubmit={async (e) => {
        e.preventDefault();
        try {
          const r = await api<{ message: string }>("/digest/subscribe", { method: "POST", body: { email } });
          setMsg(r.message);
          setEmail("");
        } catch (err) {
          setMsg(err instanceof Error ? err.message : "Please try again.");
        }
      }}
    >
      <input className="input sm:flex-1" type="email" required placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      <button className="btn btn-primary justify-center">Subscribe</button>
      {msg && <p className="text-sm text-muted sm:basis-full" role="status">{msg}</p>}
    </form>
  );
}
