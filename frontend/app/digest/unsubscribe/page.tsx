"use client";

import { useState } from "react";
import { Card } from "@/components/Field";
import { api } from "@/lib/client-api";

/** Requires an explicit click: email link scanners prefetch URLs, and that must not unsubscribe anyone. */
export default function Unsubscribe() {
  const [state, setState] = useState<"idle" | "done" | "error">("idle");
  return (
    <Card title={state === "done" ? "You're unsubscribed" : "Unsubscribe from the digest?"}>
      {state === "idle" && (
        <button
          className="btn btn-primary"
          onClick={() => {
            const token = new URLSearchParams(window.location.search).get("token") ?? "";
            api(`/digest/unsubscribe?token=${encodeURIComponent(token)}`, { method: "POST" })
              .then(() => setState("done"))
              .catch(() => setState("error"));
          }}
        >
          Unsubscribe
        </button>
      )}
      {state === "done" && <p className="text-muted">You won&apos;t get any more digest emails.</p>}
      {state === "error" && <p className="text-red-600">This link is invalid.</p>}
    </Card>
  );
}
