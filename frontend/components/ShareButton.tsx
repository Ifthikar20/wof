"use client";

import { useState } from "react";

/** Native share sheet where available, otherwise copy the link. */
export function ShareButton({ title, className = "btn btn-ghost" }: { title: string; className?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className={className}
      onClick={async () => {
        const url = window.location.href.split("?")[0];
        try {
          if (navigator.share) await navigator.share({ title, url });
          else {
            await navigator.clipboard.writeText(url);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
          }
        } catch {
          /* share cancelled */
        }
      }}
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
        <path d="M12 3v12M7 8l5-5 5 5M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6" />
      </svg>
      {copied ? "Link copied" : "Share"}
    </button>
  );
}
