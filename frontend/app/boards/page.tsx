"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { BoardCover } from "@/components/BoardCover";
import { useMe } from "@/components/SessionProvider";
import { api, fieldErrors } from "@/lib/client-api";

type Board = { id: string; name: string; is_private: boolean; save_count: number; preview: { slug: string; thumb_url: string | null }[] };

export default function BoardsPage() {
  const me = useMe();
  const [boards, setBoards] = useState<Board[] | null>(null);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api<Board[]>("/boards").then(setBoards).catch(() => setBoards([]));
  }, []);

  useEffect(() => {
    if (me === null) window.location.href = "/login?next=/boards";
    else if (me) load();
  }, [me, load]);

  if (!me) return null;

  async function create(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api("/boards", { method: "POST", body: { name } });
      setName("");
      setCreating(false);
      setError("");
      load();
    } catch (err) {
      setError(Object.values(fieldErrors(err))[0] ?? "Could not create the board.");
    }
  }

  return (
    <div className="py-4">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[.16em] text-muted">Saved</p>
          <h1 className="mt-2 font-serif text-5xl leading-none">Your boards</h1>
        </div>
        <button className="btn btn-primary h-12 px-6" onClick={() => setCreating(!creating)}>+ New board</button>
      </div>

      {creating && (
        <form onSubmit={create} className="mt-6 flex max-w-lg gap-2">
          <input className="input" autoFocus required maxLength={60} placeholder="Board name, e.g. Fundraising lessons" value={name} onChange={(e) => setName(e.target.value)} />
          <button className="btn btn-primary">Create</button>
        </form>
      )}
      {error && <p className="mt-2 text-sm text-red-600" role="alert">{error}</p>}

      <div className="mt-10 grid grid-cols-2 gap-x-5 gap-y-8 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {boards === null && <p className="col-span-full py-12 text-center text-muted">Loading…</p>}
        {boards?.length === 0 && (
          <div className="col-span-full rounded-[24px] border border-dashed border-line py-16 text-center">
            <p className="font-serif text-3xl">Nothing saved yet</p>
            <p className="mt-2 text-muted">Hover any story on the wall and hit <span className="rounded-full bg-save px-2 py-0.5 text-xs font-bold text-white">Save</span>.</p>
            <Link href="/" className="btn btn-primary mt-6">Browse the wall</Link>
          </div>
        )}
        {boards?.map((b) => (
          <Link key={b.id} href={`/boards/${b.id}`} className="group">
            <div className="transition duration-300 group-hover:-translate-y-1"><BoardCover preview={b.preview} seed={b.id} /></div>
            <p className="mt-3 font-semibold">{b.name}</p>
            <p className="text-sm text-muted">{b.save_count} {b.save_count === 1 ? "story" : "stories"} · {b.is_private ? "Private" : "Public"}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
