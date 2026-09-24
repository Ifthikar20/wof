"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/Field";
import { api } from "@/lib/client-api";

export default function ConfirmSubscription() {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token") ?? "";
    window.history.replaceState(null, "", "/digest/confirm");
    api("/digest/confirm", { method: "POST", body: { token } }).then(() => setOk(true)).catch(() => setOk(false));
  }, []);
  return (
    <Card title={ok === null ? "Confirming…" : ok ? "You're subscribed" : "Link not valid"}>
      <p className="text-muted">{ok ? "Your first digest arrives next week." : ok === false ? "This link is invalid or has expired. Subscribe again to get a fresh one." : ""}</p>
    </Card>
  );
}
