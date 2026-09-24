"use client";

import { useCallback, useState } from "react";
import { api, ApiException } from "@/lib/client-api";
import { Turnstile } from "./Turnstile";

const REASONS = [
  ["false_claim", "False founder claim or impersonation"],
  ["plagiarism", "Plagiarism / not their story"],
  ["misinformation", "Misleading or false facts"],
  ["harassment", "Harassment or hate"],
  ["spam", "Spam or advertising"],
  ["other", "Something else"],
] as const;

export function ReportButton({ targetType, targetId }: { targetType: "story" | "comment" | "user"; targetId: string }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<string>(REASONS[0][0]);
  const [details, setDetails] = useState("");
  const [token, setToken] = useState("");
  const [done, setDone] = useState("");
  const onToken = useCallback((t: string) => setToken(t), []);

  if (done) return <span className="text-sm text-muted">{done}</span>;
  if (!open) return <button className="btn btn-ghost" onClick={() => setOpen(true)}>Report</button>;

  return (
    <form
      className="mt-3 flex w-full flex-col gap-2 rounded-xl border border-line bg-surface p-4"
      onSubmit={async (e) => {
        e.preventDefault();
        try {
          await api("/reports", { method: "POST", body: { target_type: targetType, target_id: targetId, reason, details, turnstile_token: token } });
          setDone("Thanks. A moderator will review this.");
        } catch (err) {
          if (err instanceof ApiException && err.status === 403) window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
          else setDone("Could not send the report.");
        }
      }}
    >
      <select className="input" value={reason} onChange={(e) => setReason(e.target.value)}>
        {REASONS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
      </select>
      <textarea className="input" maxLength={1000} placeholder="Details (optional)" value={details} onChange={(e) => setDetails(e.target.value)} />
      <Turnstile onToken={onToken} />
      <div className="flex gap-2">
        <button className="btn btn-primary">Send report</button>
        <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </form>
  );
}
