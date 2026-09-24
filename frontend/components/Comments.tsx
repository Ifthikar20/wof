"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiException } from "@/lib/client-api";
import type { Comment, Page } from "@/lib/types";
import { Turnstile } from "./Turnstile";
import Link from "next/link";
import { Avatar } from "./Avatar";
import { VerifiedBadge } from "./VerifiedBadge";

export function Comments({ slug }: { slug: string }) {
  const [items, setItems] = useState<Comment[]>([]);
  const [body, setBody] = useState("");
  const [note, setNote] = useState("");
  const [token, setToken] = useState("");
  const onToken = useCallback((t: string) => setToken(t), []);

  useEffect(() => {
    api<Page<Comment>>(`/stories/${slug}/comments`).then((p) => setItems(p.results)).catch(() => {});
  }, [slug]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setNote("");
    try {
      const c = await api<Comment>(`/stories/${slug}/comments`, { method: "POST", body: { body, turnstile_token: token } });
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
      <h2 className="mb-5 font-serif text-3xl">Conversation {items.length > 0 && <span className="text-muted">· {items.length}</span>}</h2>
      <form onSubmit={submit} className="mb-8 rounded-[20px] border border-line bg-surface p-3 focus-within:border-ink">
        <textarea className="min-h-20 w-full resize-y bg-transparent px-2 py-1 outline-none placeholder:text-muted" maxLength={2000}
                  value={body} onChange={(e) => setBody(e.target.value)} placeholder="What did this story make you think?" required
                  aria-label="Write a comment" />
        {body.trim() && <Turnstile onToken={onToken} />}
        <div className="flex items-center justify-between gap-3 px-1">
          <span className="text-xs text-muted">{note || "Plain text. Be kind; comments are moderated."}</span>
          <button className="btn btn-primary" disabled={!body.trim()}>Post</button>
        </div>
      </form>
      <ul className="flex flex-col gap-6">
        {items.map((c) => (
          <li key={c.id} className="flex gap-3">
            <Avatar name={c.author.display_name || c.author.handle} size={36} />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 text-sm font-semibold">
                <Link href={`/f/${c.author.handle}`} className="hover:underline">{c.author.display_name || c.author.handle}</Link>
                {c.author.is_verified_founder && <VerifiedBadge />}
                <span className="font-normal text-muted">· {new Date(c.created_at).toLocaleDateString("en", { dateStyle: "medium" })}</span>
              </div>
              {/* Plain text rendered by React: automatically escaped. */}
              <p className="mt-1 whitespace-pre-wrap leading-relaxed">{c.body}</p>
            </div>
          </li>
        ))}
        {items.length === 0 && <li className="text-sm text-muted">No comments yet. Start the conversation.</li>}
      </ul>
    </section>
  );
}
