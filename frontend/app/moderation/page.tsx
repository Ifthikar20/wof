"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useMe } from "@/components/SessionProvider";
import { api, ApiException } from "@/lib/client-api";
import type { Page } from "@/lib/types";

type Verification = {
  id: string; company_name: string; company_domain: string; work_email: string; role_title: string;
  linkedin_url: string; crunchbase_url: string; notes: string; user_handle: string; created_at: string; status: string;
};
type Report = {
  id: string; reporter: string | null; target_type: "story" | "comment" | "user"; target_id: string; reason: string;
  details: string; created_at: string; target: { label: string; url: string | null; status: string; author: string | null };
};
type Held = { id: string; author: string; story: string; body: string; spam_flags: string[]; created_at: string };

const TABS = [
  { key: "verifications", label: "Verifications" },
  { key: "reports", label: "Reports" },
  { key: "comments", label: "Held comments" },
] as const;
type Tab = (typeof TABS)[number]["key"];

const REPORT_ACTIONS: Record<Report["target_type"], { action: string; label: string; danger?: boolean }[]> = {
  story: [{ action: "hide_story", label: "Hide story", danger: true }, { action: "remove_story", label: "Remove", danger: true }],
  comment: [{ action: "hide_comment", label: "Hide comment", danger: true }],
  user: [{ action: "suspend_user", label: "Suspend user", danger: true }],
};

const ago = (iso: string) => {
  const h = Math.round((Date.now() - new Date(iso).getTime()) / 36e5);
  return h < 1 ? "just now" : h < 24 ? `${h}h ago` : `${Math.round(h / 24)}d ago`;
};

/** Moderator console: every action requires a written reason and is recorded in the audit log. */
export default function ModerationPage() {
  const me = useMe();
  const [tab, setTab] = useState<Tab>("verifications");
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [held, setHeld] = useState<Held[]>([]);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [flash, setFlash] = useState("");

  const load = useCallback(async () => {
    try {
      const [v, r, c] = await Promise.all([
        api<Page<Verification>>("/moderation/verifications"),
        api<Page<Report>>("/moderation/reports"),
        api<Page<Held>>("/moderation/comments/held"),
      ]);
      setVerifications(v.results);
      setReports(r.results);
      setHeld(c.results);
      setError("");
    } catch (err) {
      setError(err instanceof ApiException ? err.message : "Could not load the queues.");
    }
  }, []);

  useEffect(() => {
    if (me === null) window.location.href = "/login?next=/moderation";
    else if (me && me.role !== "reader") load();
  }, [me, load]);

  if (!me) return null;
  if (me.role === "reader") {
    return (
      <div className="py-24 text-center">
        <h1 className="font-serif text-5xl">Moderators only</h1>
        <p className="mt-3 text-muted">This area is for the moderation team.</p>
      </div>
    );
  }

  const reason = (id: string) => reasons[id]?.trim() ?? "";
  const setReason = (id: string, v: string) => setReasons({ ...reasons, [id]: v });
  async function act(fn: () => Promise<unknown>, done: string) {
    try {
      await fn();
      setFlash(done);
      setTimeout(() => setFlash(""), 2500);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    }
  }

  const counts: Record<Tab, number> = { verifications: verifications.length, reports: reports.length, comments: held.length };

  return (
    <div className="mx-auto max-w-5xl py-4">
      <p className="text-xs font-semibold uppercase tracking-[.16em] text-muted">Moderation</p>
      <h1 className="mt-2 font-serif text-5xl leading-none">Keep the Wall honest</h1>
      <p className="mt-3 text-muted">Every decision needs a reason. Every action is recorded in the tamper-evident audit log.</p>

      <div role="tablist" className="mt-8 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button key={t.key} role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)} className={`chip gap-2 ${tab === t.key ? "chip-active" : ""}`}>
            {t.label}
            <span className={`rounded-full px-1.5 text-xs ${tab === t.key ? "bg-bg/20" : "bg-ink/10"}`}>{counts[t.key]}</span>
          </button>
        ))}
      </div>

      {error && <p className="mt-6 rounded-2xl bg-red-500/10 px-4 py-3 text-sm text-red-700" role="alert">{error}</p>}
      {flash && <p className="mt-6 rounded-2xl bg-emerald-600/10 px-4 py-3 text-sm text-emerald-800" role="status">{flash}</p>}

      <div className="mt-6 flex flex-col gap-4">
        {tab === "verifications" && verifications.length === 0 && <Empty text="No founders waiting for review." />}
        {tab === "verifications" && verifications.map((v) => (
          <article key={v.id} className="rounded-[24px] border border-line bg-surface/80 p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-serif text-3xl leading-tight">{v.company_name} <span className="text-muted">· {v.company_domain}</span></p>
                <p className="mt-1 text-sm text-muted">@{v.user_handle} claims <strong className="text-ink">{v.role_title}</strong> · {ago(v.created_at)}</p>
              </div>
              <span className="rounded-full bg-emerald-600/10 px-3 py-1 text-xs font-semibold text-emerald-700">Work email confirmed</span>
            </div>
            <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
              <div><dt className="text-muted">Work email</dt><dd className="break-all font-medium">{v.work_email}</dd></div>
              <div><dt className="text-muted">LinkedIn</dt><dd>{v.linkedin_url ? <a className="break-all underline" href={v.linkedin_url} target="_blank" rel="noopener noreferrer nofollow">Open profile ↗</a> : "—"}</dd></div>
              <div><dt className="text-muted">Crunchbase</dt><dd>{v.crunchbase_url ? <a className="break-all underline" href={v.crunchbase_url} target="_blank" rel="noopener noreferrer nofollow">Open page ↗</a> : "—"}</dd></div>
            </dl>
            {v.notes && <p className="mt-4 rounded-xl bg-chip px-4 py-3 text-sm"><span className="text-muted">Note from applicant: </span>{v.notes}</p>}
            <Checklist />
            <ReasonBox id={v.id} value={reasons[v.id] ?? ""} onChange={setReason} placeholder="Reason (shared with the applicant for rejections and info requests)" />
            <div className="mt-3 flex flex-wrap gap-2">
              {(["approve", "needs_info", "reject"] as const).map((d) => (
                <button key={d} disabled={!reason(v.id)}
                        className={`btn ${d === "approve" ? "btn-primary" : d === "reject" ? "bg-red-600 text-white hover:bg-red-700" : "btn-ghost"}`}
                        onClick={() => act(() => api(`/moderation/verifications/${v.id}/decision`, { method: "POST", body: { decision: d, reason: reason(v.id) } }),
                                           `${v.company_name}: ${d.replace("_", " ")}`)}>
                  {d === "approve" ? "Approve founder" : d === "reject" ? "Reject" : "Ask for more info"}
                </button>
              ))}
            </div>
          </article>
        ))}

        {tab === "reports" && reports.length === 0 && <Empty text="No open reports." />}
        {tab === "reports" && reports.map((r) => (
          <article key={r.id} className="rounded-[24px] border border-line bg-surface/80 p-6">
            <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[.12em]">
              <span className="rounded-full bg-red-500/10 px-2.5 py-1 text-red-700">{r.reason.replace("_", " ")}</span>
              <span className="rounded-full bg-chip px-2.5 py-1">{r.target_type}</span>
              <span className="text-muted">reported by @{r.reporter ?? "deleted user"} · {ago(r.created_at)}</span>
            </div>
            <p className="mt-3 font-serif text-2xl leading-snug">
              {r.target.url ? <Link href={r.target.url} className="hover:underline" target="_blank">{r.target.label} ↗</Link> : r.target.label}
            </p>
            <p className="text-sm text-muted">{r.target.author ? `by @${r.target.author} · ` : ""}currently {r.target.status}</p>
            {r.details && <p className="mt-3 rounded-xl bg-chip px-4 py-3 text-sm">“{r.details}”</p>}
            <ReasonBox id={r.id} value={reasons[r.id] ?? ""} onChange={setReason} placeholder="Reason for your decision" />
            <div className="mt-3 flex flex-wrap gap-2">
              {REPORT_ACTIONS[r.target_type].map((a) => (
                <button key={a.action} disabled={!reason(r.id)} className="btn bg-red-600 text-white hover:bg-red-700"
                        onClick={() => act(() => api("/moderation/actions", { method: "POST", body: { action: a.action, target_id: r.target_id, reason: reason(r.id), report_id: r.id } }), `${a.label}: done`)}>
                  {a.label}
                </button>
              ))}
              <button disabled={!reason(r.id)} className="btn btn-ghost"
                      onClick={() => act(() => api("/moderation/actions", { method: "POST", body: { action: "dismiss_report", target_id: r.target_id, reason: reason(r.id), report_id: r.id } }), "Report dismissed")}>
                Dismiss report
              </button>
            </div>
          </article>
        ))}

        {tab === "comments" && held.length === 0 && <Empty text="No comments held by the spam rules." />}
        {tab === "comments" && held.map((c) => (
          <article key={c.id} className="rounded-[24px] border border-line bg-surface/80 p-6">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {c.spam_flags.map((f) => <span key={f} className="rounded-full bg-amber-500/15 px-2.5 py-1 font-semibold text-amber-800">{f.replace(/_/g, " ")}</span>)}
              <span className="text-muted">@{c.author} on <Link className="underline" href={`/s/${c.story}`} target="_blank">{c.story}</Link> · {ago(c.created_at)}</span>
            </div>
            <p className="mt-3 whitespace-pre-wrap rounded-xl bg-chip px-4 py-3">{c.body}</p>
            <ReasonBox id={c.id} value={reasons[c.id] ?? ""} onChange={setReason} placeholder="Reason" />
            <div className="mt-3 flex gap-2">
              <button disabled={!reason(c.id)} className="btn btn-primary"
                      onClick={() => act(() => api("/moderation/actions", { method: "POST", body: { action: "approve_comment", target_id: c.id, reason: reason(c.id) } }), "Comment approved")}>
                Approve
              </button>
              <button disabled={!reason(c.id)} className="btn bg-red-600 text-white hover:bg-red-700"
                      onClick={() => act(() => api("/moderation/actions", { method: "POST", body: { action: "hide_comment", target_id: c.id, reason: reason(c.id) } }), "Comment hidden")}>
                Hide
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function ReasonBox(props: { id: string; value: string; onChange: (id: string, v: string) => void; placeholder: string }) {
  return (
    <textarea className="input mt-5 min-h-16 text-sm" maxLength={500} placeholder={props.placeholder} aria-label="Reason"
              value={props.value} onChange={(e) => props.onChange(props.id, e.target.value)} />
  );
}

function Checklist() {
  return (
    <details className="mt-4 text-sm">
      <summary className="cursor-pointer font-semibold">Review checklist</summary>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
        <li>Profile names the same person and a <em>founder</em> role at this company</li>
        <li>Company domain matches the real website (Crunchbase / LinkedIn company page)</li>
        <li>Company is real: registry entry, product site or press</li>
        <li>Red flags: brand-new domain, lookalike domain, mismatched names, prior rejections</li>
      </ul>
    </details>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="rounded-[24px] border border-dashed border-line py-16 text-center">
      <p className="font-serif text-3xl">All clear</p>
      <p className="mt-1 text-muted">{text}</p>
    </div>
  );
}
