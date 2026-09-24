"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/Field";
import { api, ApiException } from "@/lib/client-api";

export default function ConfirmWorkEmail() {
  const [state, setState] = useState<"working" | "ok" | "error">("working");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token") ?? "";
    // Strip the token from the address bar / history as soon as we've read it.
    window.history.replaceState(null, "", "/verify/confirm");
    api("/verification/confirm-email", { method: "POST", body: { token } })
      .then(() => setState("ok"))
      .catch((err) => {
        if (err instanceof ApiException && err.status === 403) {
          window.location.href = `/login?next=${encodeURIComponent(`/verify/confirm?token=${token}`)}`;
          return;
        }
        setMessage(err instanceof Error ? err.message : "");
        setState("error");
      });
  }, []);

  return (
    <Card title={state === "ok" ? "Email confirmed" : state === "error" ? "Link not valid" : "Confirming…"}>
      <p className="text-muted">
        {state === "ok" && "Thanks! Your evidence is now with a human moderator. We'll email you when there's a decision."}
        {state === "error" && (message || "This link is invalid or expired. Start again from the verification page.")}
      </p>
    </Card>
  );
}
