"use client";

import { useState } from "react";
import { ApiException } from "@/lib/client-api";
import { saveStory } from "@/lib/boards";

/** Pinterest-style red "Save" pill shown on a card's hover overlay. */
export function SaveButton({ slug }: { slug: string }) {
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");

  async function onClick(e: React.MouseEvent) {
    e.preventDefault(); // the overlay sits on top of the card link
    e.stopPropagation();
    if (state !== "idle") return;
    setState("saving");
    try {
      await saveStory(slug);
      setState("saved");
    } catch (err) {
      if (err instanceof ApiException && (err.status === 401 || err.status === 403)) {
        window.location.href = `/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
        return;
      }
      setState("idle");
    }
  }

  return (
    <button
      onClick={onClick}
      aria-label={state === "saved" ? "Saved" : "Save story"}
      className={`pointer-events-auto rounded-full px-4 py-2.5 text-sm font-bold text-white shadow-sm transition ${
        state === "saved" ? "bg-black" : "bg-save hover:brightness-90"
      }`}
    >
      {state === "saved" ? "Saved" : state === "saving" ? "Saving…" : "Save"}
    </button>
  );
}
