"use client";

import { useState } from "react";
import { api } from "@/lib/client-api";

type Upload = { media_id: string; upload: { url: string; fields: Record<string, string> } };
type Media = { id: string; status: string; thumb_url: string | null; rejection_reason: string };

const MAX_BYTES = 10 * 1024 * 1024;
const TYPES = ["image/jpeg", "image/png", "image/webp"];

/**
 * 1) ask the API for a presigned POST (private bucket, pinned key/type/size, 5-min expiry)
 * 2) upload straight to object storage (the API never buffers file bytes)
 * 3) tell the API it's done; a worker re-encodes and strips metadata; poll until ready.
 */
export function CoverUpload({ onReady }: { onReady: (id: string | null) => void }) {
  const [status, setStatus] = useState("");
  const [preview, setPreview] = useState<string | null>(null);

  async function handle(file: File) {
    if (!TYPES.includes(file.type)) return setStatus("Use a JPEG, PNG or WebP image.");
    if (file.size > MAX_BYTES) return setStatus("Images must be under 10 MB.");
    setStatus("Uploading…");
    const { media_id, upload } = await api<Upload>("/media/uploads", { method: "POST", body: { content_type: file.type } });
    const body = new FormData();
    Object.entries(upload.fields).forEach(([k, v]) => body.append(k, v));
    body.append("file", file);
    const put = await fetch(upload.url, { method: "POST", body });
    if (!put.ok) return setStatus("Upload failed.");
    await api(`/media/${media_id}/complete`, { method: "POST" });
    setStatus("Processing…");
    for (let i = 0; i < 30; i++) {
      await new Promise((r) => setTimeout(r, 1000));
      const m = await api<Media>(`/media/${media_id}`);
      if (m.status === "ready") {
        setPreview(m.thumb_url);
        setStatus("");
        return onReady(m.id);
      }
      if (m.status === "rejected") return setStatus(m.rejection_reason || "Image rejected.");
    }
    setStatus("Still processing, try again shortly.");
  }

  const pick = (file?: File) => file && handle(file).catch(() => setStatus("Upload failed."));

  return (
    <label
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files?.[0]); }}
      className="group flex cursor-pointer items-center gap-4 rounded-2xl p-1 focus-within:ring-2 focus-within:ring-ink"
    >
      {preview ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={preview} alt="" className="h-20 w-32 rounded-xl object-cover" />
      ) : (
        <span className="grid h-20 w-32 place-items-center rounded-xl bg-chip text-muted transition group-hover:bg-ink/10" aria-hidden>
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.7">
            <rect x="3" y="4" width="18" height="16" rx="3" /><circle cx="9" cy="10" r="1.8" /><path d="m21 16-5-5-9 9" />
          </svg>
        </span>
      )}
      <span className="flex flex-col">
        <span className="font-semibold">{preview ? "Replace image" : "Upload a cover image"}</span>
        <span className="text-sm text-muted">{status || "Drag & drop or click · JPEG, PNG or WebP · up to 10 MB"}</span>
      </span>
      <input type="file" className="sr-only" accept={TYPES.join(",")} onChange={(e) => pick(e.target.files?.[0])} />
    </label>
  );
}
