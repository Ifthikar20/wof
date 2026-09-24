"use client";

import { useEffect, useState } from "react";
import { StoryCard } from "@/components/StoryCard";
import { api, ApiException } from "@/lib/client-api";
import type { StoryCard as Story } from "@/lib/types";

type Board = { id: string; name: string; save_count: number; stories?: Story[] };

export default function BoardsPage() {
  const [boards, setBoards] = useState<Board[] | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const list = await api<Board[]>("/boards");
        setBoards(await Promise.all(list.map((b) => api<Board>(`/boards/${b.id}`))));
      } catch (err) {
        if (err instanceof ApiException && err.status === 403) window.location.href = "/login?next=/boards";
      }
    })();
  }, []);

  if (!boards) return <p className="py-16 text-center text-muted">Loading…</p>;
  if (!boards.length) return <p className="py-16 text-center text-muted">Nothing saved yet. Tap “Save” on any story.</p>;

  return (
    <div className="flex flex-col gap-10">
      {boards.map((b) => (
        <section key={b.id}>
          <h2 className="mb-4 font-serif text-2xl">{b.name} <span className="text-base font-normal text-muted">· {b.save_count}</span></h2>
          <div className="wall">{b.stories?.map((s) => <StoryCard key={s.slug} story={s} />)}</div>
        </section>
      ))}
    </div>
  );
}
