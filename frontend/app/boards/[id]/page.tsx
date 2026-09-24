"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ShareButton } from "@/components/ShareButton";
import { StoryCard } from "@/components/StoryCard";
import { api, ApiException } from "@/lib/client-api";
import type { StoryCard as Story } from "@/lib/types";

type Board = { id: string; name: string; description: string; is_private: boolean; save_count: number; stories: Story[]; owner: string; is_owner: boolean };

export default function BoardPage() {
  const { id } = useParams<{ id: string }>();
  const [board, setBoard] = useState<Board | null | undefined>(undefined);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState("");

  const load = useCallback(() => {
    if (!/^[0-9a-f-]{36}$/.test(id)) return setBoard(null);
    api<Board>(`/boards/${id}`).then((b) => { setBoard(b); setName(b.name); }).catch((err) => {
      if (err instanceof ApiException && err.status === 404) setBoard(null);
    });
  }, [id]);

  useEffect(load, [load]);

  if (board === undefined) return <p className="py-24 text-center text-muted">Loading…</p>;
  if (board === null) {
    return (
      <div className="py-24 text-center">
        <h1 className="font-serif text-5xl">Board not found</h1>
        <p className="mt-2 text-muted">It may be private, or it no longer exists.</p>
      </div>
    );
  }

  async function update(body: Partial<Board>) {
    await api(`/boards/${id}`, { method: "PATCH", body });
    load();
  }

  return (
    <div className="py-4">
      <div className="mx-auto flex max-w-3xl flex-col items-center text-center">
        {board.is_owner && <Link href="/boards" className="mb-6 text-sm font-semibold text-muted hover:text-ink">← All boards</Link>}
        {editing ? (
          <form className="flex w-full max-w-md gap-2" onSubmit={async (e) => { e.preventDefault(); await update({ name }); setEditing(false); }}>
            <input className="input text-center text-xl" autoFocus maxLength={60} required value={name} onChange={(e) => setName(e.target.value)} />
            <button className="btn btn-primary">Save</button>
          </form>
        ) : (
          <h1 className="font-serif text-6xl leading-none">{board.name}</h1>
        )}
        <p className="mt-3 text-muted">
          {board.save_count} {board.save_count === 1 ? "story" : "stories"} · {board.is_private ? "Private" : "Public"} · by @{board.owner}
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {board.is_owner && (
            <>
              <button className="btn btn-ghost" onClick={() => setEditing(!editing)}>Rename</button>
              <button className="btn btn-ghost" onClick={() => update({ is_private: !board.is_private })}>
                {board.is_private ? "Make public" : "Make private"}
              </button>
              <button className="btn btn-ghost text-red-600" onClick={async () => {
                if (!window.confirm(`Delete “${board.name}”? Stories stay on the wall.`)) return;
                await api(`/boards/${id}`, { method: "DELETE" });
                window.location.href = "/boards";
              }}>Delete</button>
            </>
          )}
          {!board.is_private && <ShareButton title={board.name} />}
        </div>
      </div>

      <div className="wall mt-12">
        {board.stories.map((s) => (
          <div key={s.slug} className="relative">
            <StoryCard story={s} />
            {board.is_owner && (
              <button onClick={async () => { await api(`/boards/${id}/saves/${s.slug}`, { method: "DELETE" }); load(); }}
                      className="absolute left-2 top-2 z-10 rounded-full bg-white/90 px-3 py-1.5 text-xs font-semibold text-black shadow hover:bg-white">
                Remove
              </button>
            )}
          </div>
        ))}
      </div>
      {board.stories.length === 0 && <p className="py-16 text-center text-muted">This board is empty.</p>}
    </div>
  );
}
