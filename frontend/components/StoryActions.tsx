"use client";

import Link from "next/link";
import { useState } from "react";
import { api, ApiException } from "@/lib/client-api";
import { saveStory } from "@/lib/boards";
import { ReportButton } from "./ReportButton";

export function StoryActions(props: { slug: string; storyId: string; initialLiked: boolean; likeCount: number; isAuthor: boolean; status: string }) {
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
      const target = await saveStory(props.slug);
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
    <div className="mt-12 flex flex-wrap items-center gap-2 border-t border-line pt-6">
      {props.status === "published" && (
        <>
          <button onClick={toggleLike} aria-pressed={liked} aria-label={liked ? "Unlike" : "Like"}
                  className={`btn ${liked ? "bg-save text-white hover:brightness-95" : "btn-ghost"}`}>
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill={liked ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" aria-hidden>
              <path d="M12 20s-7-4.4-9.2-8.6C1.2 8.3 3 5 6.3 5c2 0 3.3 1.1 3.9 2.2l1.8 2 1.8-2C14.4 6.1 15.7 5 17.7 5 21 5 22.8 8.3 21.2 11.4 19 15.6 12 20 12 20Z" />
            </svg>
            {count}
          </button>
          <button onClick={save} className="btn bg-save text-white hover:brightness-95">Save</button>
        </>
      )}
      {props.isAuthor && (
        <>
          <Link href={`/write?slug=${props.slug}`} className="btn btn-ghost">Edit story</Link>
          {props.status === "draft" && <button onClick={publish} className="btn btn-primary">Publish</button>}
        </>
      )}
      {message && <span className="text-sm text-muted">{message}</span>}
      {props.status === "published" && !props.isAuthor && (
        <div className="ml-auto"><ReportButton targetType="story" targetId={props.storyId} /></div>
      )}
    </div>
  );
}
