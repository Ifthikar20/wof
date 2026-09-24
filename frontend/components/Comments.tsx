"use client";

import { useEffect, useState } from "react";
import { api, ApiException } from "@/lib/client-api";
import type { Comment, Page } from "@/lib/types";
import { VerifiedBadge } from "./VerifiedBadge";

export function Comments({ slug }: { slug: string }) {
  const [items, setItems] = useState<Comment[]>([]);
  const [body, setBody] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    api<Page<Comment>>(`/stories/${slug}/comments`).then((p) => setItems(p.results)).catch(() => {});
  }, [slug]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setNote("");
    try {
      const c = await api<Comment>(`/stories/${slug}/comments`, { method: "POST", body: { body } });
      setBody("");
      if (c.status === "visible") setItems((xs) => [c, ...xs]);
      else setNote("Thanks! Your comment is waiting for review.");
    } catch (err) {
      if (err instanceof ApiException && err.status === 403) setNote("Log in to join the conversation.");
      else setNote(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <section className="mt-12">
      <h2 className="mb-4 text-lg font-bold">Conversation</h2>
      <form onSubmit={submit} className="mb-6 flex flex-col gap-2">
        <textarea className="input min-h-24" maxLength={2000} value={body} onChange={(e) => setBody(e.target.value)}
                  placeholder="What did this story make you think?" required />
        <div className="flex items-center gap-3">
          <button className="btn btn-primary" disabled={!body.trim()}>Post</button>
          {note && <span className="text-sm text-muted">{note}</span>}
        </div>
      </form>
      <ul className="flex flex-col gap-4">
        {items.map((c) => (
          <li key={c.id} className="rounded-xl border border-line bg-surface p-4">
            <div className="mb-1 flex items-center gap-1.5 text-sm font-semibold">
              {c.author.display_name || c.author.handle} {c.author.is_verified_founder && <VerifiedBadge />}
              <span className="font-normal text-muted">· {new Date(c.created_at).toLocaleDateString()}</span>
            </div>
            {/* Plain text rendered by React: automatically escaped. */}
            <p className="whitespace-pre-wrap">{c.body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
