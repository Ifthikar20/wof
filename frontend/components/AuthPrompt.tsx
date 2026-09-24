"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { isBot, isExemptPath, loadState, nextPrompt, saveState } from "@/lib/auth-prompt";
import { useMe } from "./SessionProvider";

/**
 * Sign-up prompt for logged-out visitors, shown after a delay. The first one can be
 * closed; the next one can't. Sign-up, log-in and token pages are exempt, so the firm
 * prompt never blocks anyone from completing those flows. (UX, not security: see lib/auth-prompt.ts.)
 */
export function AuthPrompt() {
  const me = useMe();
  const path = usePathname();
  const [mode, setMode] = useState<"soft" | "firm" | null>(null);
  const [dismissals, setDismissals] = useState(0); // re-runs scheduling after a dismissal
  const dialogRef = useRef<HTMLDivElement>(null);

  // Schedule the next prompt whenever we land on a page as a logged-out visitor.
  useEffect(() => {
    setMode(null);
    if (me !== null || isExemptPath(path) || isBot(navigator.userAgent)) return;
    const { mode: next, dueAt } = nextPrompt(loadState(Date.now()));
    const timer = window.setTimeout(() => setMode(next), Math.max(0, dueAt - Date.now()));
    return () => window.clearTimeout(timer); // no stray timers across navigation
  }, [me, path, dismissals]);

  // While open: move focus in, trap Tab, handle Escape; firm mode locks the page behind.
  useEffect(() => {
    if (!mode) return;
    const dialog = dialogRef.current;
    dialog?.querySelector<HTMLElement>("a,button")?.focus();
    const background = [document.querySelector("main"), document.querySelector("header")];
    if (mode === "firm") {
      document.body.style.overflow = "hidden";
      background.forEach((el) => el?.setAttribute("inert", ""));
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && mode === "soft") dismiss();
      if (e.key === "Tab" && dialog) {
        const items = [...dialog.querySelectorAll<HTMLElement>("a,button")];
        const first = items[0];
        const last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
      background.forEach((el) => el?.removeAttribute("inert"));
    };
  }, [mode]);

  function dismiss() {
    const state = loadState(Date.now());
    saveState({ ...state, softDismissedAt: Date.now() });
    setDismissals((n) => n + 1);
  }

  if (!mode) return null;
  const next = encodeURIComponent(path);

  return (
    <div
      className={`fixed inset-0 z-50 grid place-items-center p-4 ${mode === "firm" ? "bg-black/60 backdrop-blur-md" : "bg-black/40"}`}
      onClick={mode === "soft" ? dismiss : undefined}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-prompt-title"
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-md rounded-3xl bg-surface px-8 pb-8 pt-10 text-center shadow-2xl"
      >
        {mode === "soft" && (
          <button aria-label="Close" onClick={dismiss} className="absolute right-4 top-4 grid h-10 w-10 place-items-center rounded-full hover:bg-chip">
            ✕
          </button>
        )}
        <span className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-accent text-lg font-bold text-accent-ink">W</span>
        <h2 id="auth-prompt-title" className="mt-4 font-serif text-3xl font-bold leading-tight">
          {mode === "firm" ? "Join to keep reading" : "See every founder story. Join the Wall."}
        </h2>
        <p className="mt-2 text-muted">
          Free for readers. Founders get verified and tell their own story.
        </p>
        <div className="mt-6 flex flex-col gap-3">
          <Link href={`/signup?next=${next}`} className="rounded-full bg-save px-5 py-3 font-bold text-white hover:brightness-90">
            Join as a reader
          </Link>
          <Link href="/signup?intent=founder&next=%2Fverify" className="rounded-full bg-chip px-5 py-3 font-bold hover:brightness-95">
            I&apos;m a founder
          </Link>
        </div>
        <p className="mt-5 text-sm text-muted">
          Already a member?{" "}
          <Link href={`/login?next=${next}`} className="font-semibold text-ink underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
