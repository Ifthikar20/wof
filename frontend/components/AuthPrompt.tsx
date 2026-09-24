"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { isBot, isExemptPath, loadState, nextPrompt, saveState } from "@/lib/auth-prompt";
import { LoginForm } from "./LoginForm";
import { LogoMark } from "./Logo";
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
    (dialog?.querySelector<HTMLElement>("input") ?? dialog?.querySelector<HTMLElement>("a,button"))?.focus();
    const background = [document.querySelector("main"), document.querySelector("header")];
    if (mode === "firm") {
      document.body.style.overflow = "hidden";
      background.forEach((el) => el?.setAttribute("inert", ""));
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && mode === "soft") dismiss();
      if (e.key === "Tab" && dialog) {
        const items = [...dialog.querySelectorAll<HTMLElement>("a[href],button,input")];
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
      className={`fixed inset-0 z-50 grid place-items-center overflow-y-auto p-4 ${mode === "firm" ? "bg-black/55 backdrop-blur-md" : "bg-black/45 backdrop-blur-[2px]"}`}
      onClick={mode === "soft" ? dismiss : undefined}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-prompt-title"
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-[440px] rounded-[32px] bg-surface p-8 shadow-[0_40px_120px_-30px_rgba(0,0,0,.6)] sm:p-10"
      >
        {mode === "soft" && (
          <button aria-label="Close" onClick={dismiss} className="absolute right-5 top-5 grid h-10 w-10 place-items-center rounded-full text-muted hover:bg-chip hover:text-ink">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden><path d="M6 6l12 12M18 6 6 18" /></svg>
          </button>
        )}
        <span className="grid h-14 w-14 place-items-center rounded-2xl bg-chip">
          <LogoMark className="h-8 w-8" />
        </span>
        <h2 id="auth-prompt-title" className="mt-5 font-serif text-[2.6rem] leading-[1.02]">
          {mode === "firm" ? "Keep reading with a free account" : "Welcome to Wall of Founders"}
        </h2>
        <p className="mb-6 mt-2 text-muted">Log in to save stories and follow the founders behind them.</p>

        <LoginForm onSuccess={() => window.location.reload()} />

        <div className="my-5 flex items-center gap-3 text-xs font-semibold uppercase tracking-[.14em] text-muted">
          <span className="h-px flex-1 bg-line" />or<span className="h-px flex-1 bg-line" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Link href={`/signup?next=${next}`} className="btn btn-outline h-12">Join as a reader</Link>
          <Link href="/signup?intent=founder&next=%2Fverify" className="btn btn-outline h-12">I&apos;m a founder</Link>
        </div>
        <p className="mt-6 text-center text-xs text-muted">
          Free for readers. Founders are verified by a person before they can publish.
        </p>
      </div>
    </div>
  );
}
