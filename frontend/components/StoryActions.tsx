"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiException } from "@/lib/client-api";

type Board = { id: string; name: string };

export function StoryActions(props: { slug: string; initialLiked: boolean; likeCount: number; isAuthor: boolean; status: string }) {
  const [liked, setLiked] = useState(props.initialLiked);
  const [count, setCount] = useState(props.likeCount);
  const [message, setMessage] = useState("");

  function needLogin(err: unknown) {
    if (err instanceof ApiException && (err.status === 401 || err.status === 403)) {
      window.location.href = `/login?next=/s/${props.slug}`;
      return true;
    }
    return false;
  }

  async function toggleLike() {
    try {
      await api(`/stories/${props.slug}/like`, { method: liked ? "DELETE" : "POST" });
      setCount((c) => c + (liked ? -1 : 1));
      setLiked(!liked);
    } catch (err) {
      needLogin(err);
    }
  }

  async function save() {
    try {
      const boards = await api<Board[]>("/boards");
      const target = boards[0] ?? (await api<Board>("/boards", { method: "POST", body: { name: "Saved stories" } }));
      await api(`/boards/${target.id}/saves`, { method: "POST", body: { story: props.slug } });
      setMessage(`Saved to “${target.name}”`);
    } catch (err) {
      if (!needLogin(err)) setMessage("Could not save.");
    }
  }

  async function publish() {
    await api(`/stories/${props.slug}/publish`, { method: "POST" });
    window.location.reload();
  }

  return (
    <div className="mt-10 flex flex-wrap items-center gap-2 border-t border-line pt-6">
      {props.status === "published" && (
        <>
          <button onClick={toggleLike} className={`btn ${liked ? "btn-primary" : "btn-ghost"}`} aria-pressed={liked}>
            ♥ {count}
          </button>
          <button onClick={save} className="btn btn-ghost">Save</button>
        </>
      )}
      {props.isAuthor && (
        <>
          <Link href={`/write?slug=${props.slug}`} className="btn btn-ghost">Edit</Link>
          {props.status === "draft" && <button onClick={publish} className="btn btn-primary">Publish</button>}
        </>
      )}
      {message && <span className="text-sm text-muted">{message}</span>}
    </div>
  );
}
