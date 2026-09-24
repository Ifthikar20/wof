"use client";

import { useState } from "react";
import type { Page, StoryCard as Story } from "@/lib/types";
import { StoryCard } from "./StoryCard";

/** Server renders the first page (fast, crawlable); this appends later pages by cursor. */
export function Wall({ initial }: { initial: Page<Story> }) {
  const [stories, setStories] = useState(initial.results);
  const [next, setNext] = useState(initial.next);
  const [loading, setLoading] = useState(false);

  async function loadMore() {
    if (!next) return;
    setLoading(true);
    try {
      const url = new URL(next, window.location.origin);
      const res = await fetch(`/api/v1/stories${url.search}`, { credentials: "same-origin" });
      if (!res.ok) throw new Error(String(res.status));
      const page: Page<Story> = await res.json();
      setStories((s) => [...s, ...page.results]);
      setNext(page.next);
    } finally {
      setLoading(false);
    }
  }

  if (stories.length === 0) {
    return <p className="py-24 text-center text-muted">No stories here yet.</p>;
  }

  return (
    <>
      <div className="wall">
        {stories.map((s) => (
          <StoryCard key={s.slug} story={s} />
        ))}
      </div>
      {next && (
        <div className="flex justify-center py-8">
          <button onClick={loadMore} disabled={loading} className="btn btn-ghost">
            {loading ? "Loading…" : "Show more stories"}
          </button>
        </div>
      )}
    </>
  );
}
