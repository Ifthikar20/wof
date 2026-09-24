"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { CoverUpload } from "@/components/CoverUpload";
import { FounderGate } from "@/components/FounderGate";
import { useMe } from "@/components/SessionProvider";
import { api, ApiException, fieldErrors } from "@/lib/client-api";
import type { StoryDetail, Tag } from "@/lib/types";

/** Distraction-free editor: borderless title and body, a slim sticky toolbar, topics below. */
export default function WritePage() {
  const me = useMe();
  const [slug, setSlug] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("new");
  const [form, setForm] = useState({ title: "", dek: "", body_markdown: "" });
  const [tags, setTags] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<Tag[]>([]);
  const [coverId, setCoverId] = useState<string | null | undefined>(undefined);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [help, setHelp] = useState(false);
  const titleRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (me === null) window.location.href = "/login?next=/write";
  }, [me]);

  useEffect(() => {
    api<Tag[]>("/tags").then(setAllTags).catch(() => {});
    const s = new URLSearchParams(window.location.search).get("slug");
    if (s && /^[a-z0-9-]{1,120}$/.test(s)) {
      api<StoryDetail & { body_markdown?: string }>(`/stories/${s}`).then((st) => {
        setSlug(st.slug);
        setStatus(st.status);
        setForm({ title: st.title, dek: st.dek, body_markdown: st.body_markdown ?? "" });
        setTags(st.tags);
      });
    }
  }, []);

  // Auto-grow the title field.
  useEffect(() => {
    const el = titleRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    }
  }, [form.title]);

  if (!me) return null;
  if (!me.is_verified_founder || !me.totp_enabled) return <FounderGate me={me} />;

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm({ ...form, [k]: e.target.value });
  const words = form.body_markdown.trim() ? form.body_markdown.trim().split(/\s+/).length : 0;

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    setBusy(true);
    const body: Record<string, unknown> = { ...form, tags };
    if (coverId !== undefined) body.cover_id = coverId;
    try {
      const story = await api<StoryDetail>(slug ? `/stories/${slug}` : "/stories", { method: slug ? "PATCH" : "POST", body });
      window.location.href = `/s/${story.slug}`;
    } catch (err) {
      const fe = fieldErrors(err);
      if (err instanceof ApiException && !Object.keys(fe).length) fe.form = err.message;
      setErrors(fe);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save} className="mx-auto max-w-3xl">
      {/* Toolbar */}
      <div className="glass sticky top-[65px] z-10 -mx-4 mb-10 flex items-center gap-3 border-b border-line/60 px-4 py-3 sm:mx-0 sm:rounded-full sm:border sm:px-5">
        <Link href="/studio" className="text-sm font-semibold text-muted hover:text-ink">← Studio</Link>
        <span className="rounded-full bg-chip px-2.5 py-1 text-xs font-semibold capitalize">{status === "new" ? "New draft" : status}</span>
        <span className="hidden text-sm text-muted sm:inline">{words} words · ~{Math.max(1, Math.ceil(words / 230))} min read</span>
        <button className="btn btn-primary ml-auto" disabled={busy}>
          {busy ? "Saving…" : slug ? "Save revision" : "Save draft"}
        </button>
      </div>

      {slug && status === "published" && (
        <p className="mb-6 rounded-2xl bg-chip px-4 py-3 text-sm">
          This story is live. Saving creates a new revision; the change is recorded in its public edit history.
        </p>
      )}

      <label htmlFor="title" className="sr-only">Title</label>
      <textarea id="title" ref={titleRef} rows={1} maxLength={140} required placeholder="Title"
                value={form.title} onChange={set("title")}
                className="w-full resize-none overflow-hidden bg-transparent font-serif text-[clamp(2.5rem,5vw,4rem)] leading-[1.05] outline-none placeholder:text-muted/50" />
      {errors.title && <p className="text-sm text-red-600">{errors.title}</p>}

      <label htmlFor="dek" className="sr-only">Subtitle</label>
      <input id="dek" maxLength={280} placeholder="One sentence that makes people want to read…" value={form.dek} onChange={set("dek")}
             className="mt-3 w-full bg-transparent text-xl text-muted outline-none placeholder:text-muted/50" />

      <div className="my-8 rounded-[20px] border border-dashed border-line p-5">
        <p className="mb-3 text-sm font-semibold">Cover image <span className="font-normal text-muted">(optional; shown full-frame at the top)</span></p>
        <CoverUpload onReady={setCoverId} />
      </div>

      <div className="mb-2 flex items-center justify-between">
        <label htmlFor="body" className="text-sm font-semibold">Your story</label>
        <button type="button" onClick={() => setHelp(!help)} className="text-sm text-muted underline underline-offset-4">
          {help ? "Hide formatting" : "Formatting help"}
        </button>
      </div>
      {help && (
        <div className="mb-3 grid grid-cols-2 gap-x-6 gap-y-1 rounded-2xl bg-chip p-4 font-mono text-xs sm:grid-cols-3">
          <span>## Heading</span><span>**bold**</span><span>*italic*</span>
          <span>&gt; Quote</span><span>- List item</span><span>[link](https://…)</span>
        </div>
      )}
      <textarea id="body" maxLength={60000} required placeholder="Start with the moment everything changed…"
                value={form.body_markdown} onChange={set("body_markdown")}
                className="min-h-[55vh] w-full resize-y bg-transparent text-[1.2rem] leading-[1.8] outline-none placeholder:text-muted/50"
                style={{ fontFamily: "var(--font-read)" }} />
      {errors.body_markdown && <p className="text-sm text-red-600">{errors.body_markdown}</p>}

      <fieldset className="mt-8 border-t border-line pt-6">
        <legend className="mb-3 text-sm font-semibold">Topics <span className="font-normal text-muted">({tags.length}/5)</span></legend>
        <div className="flex flex-wrap gap-2">
          {allTags.map((t) => {
            const on = tags.includes(t.slug);
            return (
              <button type="button" key={t.slug} className={`chip ${on ? "chip-active" : ""}`} aria-pressed={on}
                      onClick={() => setTags(on ? tags.filter((x) => x !== t.slug) : tags.length < 5 ? [...tags, t.slug] : tags)}>
                {t.name}
              </button>
            );
          })}
        </div>
      </fieldset>
      {errors.form && <p className="mt-4 text-sm text-red-600" role="alert">{errors.form}</p>}
      <p className="mt-10 text-center text-sm text-muted">Drafts are private. You can review a draft on its own page before publishing.</p>
    </form>
  );
}
