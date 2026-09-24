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

  return (
    <div className="flex items-center gap-4">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      {preview && <img src={preview} alt="" className="h-16 w-24 rounded-lg object-cover" />}
      <input type="file" accept={TYPES.join(",")} onChange={(e) => e.target.files?.[0] && handle(e.target.files[0]).catch(() => setStatus("Upload failed."))} />
      {status && <span className="text-sm text-muted">{status}</span>}
    </div>
  );
}
