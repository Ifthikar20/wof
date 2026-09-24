"use client";

import { useEffect, useState } from "react";
import { CoverUpload } from "@/components/CoverUpload";
import { Field } from "@/components/Field";
import { api, ApiException, fieldErrors } from "@/lib/client-api";
import type { Me, StoryDetail, Tag } from "@/lib/types";

export default function WritePage() {
  const [me, setMe] = useState<Me | null>(null);
  const [slug, setSlug] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", dek: "", body_markdown: "" });
  const [tags, setTags] = useState<string[]>([]);
  const [allTags, setAllTags] = useState<Tag[]>([]);
  const [coverId, setCoverId] = useState<string | null | undefined>(undefined);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState("");

  useEffect(() => {
    api<Me | null>("/auth/me").then((m) => (m ? setMe(m) : (window.location.href = "/login?next=/write")));
    api<Tag[]>("/tags").then(setAllTags).catch(() => {});
    const s = new URLSearchParams(window.location.search).get("slug");
    if (s && /^[a-z0-9-]{1,120}$/.test(s)) {
      api<StoryDetail & { body_markdown?: string }>(`/stories/${s}`).then((st) => {
        setSlug(st.slug);
        setForm({ title: st.title, dek: st.dek, body_markdown: st.body_markdown ?? "" });
        setTags(st.tags);
        setSaved("Editing a published story creates a new, publicly hashed revision.");
      });
    }
  }, []);

  if (me && !me.is_verified_founder) {
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <h1 className="font-serif text-2xl">Only verified founders can publish</h1>
        <p className="mt-2 text-muted">It keeps the Wall trustworthy. Verification takes a couple of minutes to submit.</p>
        <a href="/verify" className="btn btn-primary mt-6">Verify that you&apos;re a founder</a>
      </div>
    );
  }

  if (me && me.is_verified_founder && !me.totp_enabled) {
    // Publishing requires 2FA (REQUIRE_2FA_FOR_FOUNDERS); surface that up front.
    return (
      <div className="mx-auto max-w-lg py-16 text-center">
        <h1 className="font-serif text-2xl">One more step: turn on 2FA</h1>
        <p className="mt-2 text-muted">Founder accounts need two-factor authentication so nobody can publish in your name.</p>
        <a href="/settings/security" className="btn btn-primary mt-6">Set up two-factor authentication</a>
      </div>
    );
  }

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setForm({ ...form, [k]: e.target.value });

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    const body: Record<string, unknown> = { ...form, tags };
    if (coverId !== undefined) body.cover_id = coverId;
    try {
      const story = await api<StoryDetail>(slug ? `/stories/${slug}` : "/stories", { method: slug ? "PATCH" : "POST", body });
      window.location.href = `/s/${story.slug}`;
    } catch (err) {
      const fe = fieldErrors(err);
      if (err instanceof ApiException && !Object.keys(fe).length) fe.form = err.message;
      setErrors(fe);
    }
  }

  return (
    <form onSubmit={save} className="mx-auto flex max-w-2xl flex-col gap-5">
      <h1 className="font-serif text-3xl">{slug ? "Edit your story" : "Tell your story"}</h1>
      {saved && <p className="text-sm text-muted">{saved}</p>}
      <Field label="Title" error={errors.title}><input className="input text-lg" maxLength={140} required value={form.title} onChange={set("title")} /></Field>
      <Field label="Subtitle" error={errors.dek} hint="One sentence that makes people want to read."><input className="input" maxLength={280} value={form.dek} onChange={set("dek")} /></Field>
      <Field label="Cover image (optional)"><CoverUpload onReady={setCoverId} /></Field>
      <Field label="Story" error={errors.body_markdown} hint="Markdown supported: ## headings, **bold**, > quotes, lists, links.">
        <textarea className="input min-h-[420px] font-serif text-lg leading-relaxed" maxLength={60000} required value={form.body_markdown} onChange={set("body_markdown")} />
      </Field>
      <fieldset>
        <legend className="mb-2 text-sm font-semibold">Topics (up to 5)</legend>
        <div className="flex flex-wrap gap-2">
          {allTags.map((t) => {
            const on = tags.includes(t.slug);
            return (
              <button type="button" key={t.slug} className={`btn ${on ? "btn-primary" : "btn-ghost"}`} aria-pressed={on}
                      onClick={() => setTags(on ? tags.filter((x) => x !== t.slug) : tags.length < 5 ? [...tags, t.slug] : tags)}>
                {t.name}
              </button>
            );
          })}
        </div>
      </fieldset>
      {errors.form && <p className="text-sm text-red-600" role="alert">{errors.form}</p>}
      <div className="flex gap-3">
        <button className="btn btn-primary">{slug ? "Save revision" : "Save draft"}</button>
        <span className="self-center text-sm text-muted">You can review the draft before publishing.</span>
      </div>
    </form>
  );
}
