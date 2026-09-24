"use client";

import { useSearchParams } from "next/navigation";

/** Big grey pill search. A plain GET form: works before hydration and without JS. */
export function SearchBar() {
  const q = useSearchParams().get("q") ?? "";
  return (
    <form action="/" method="get" role="search" className="min-w-0 flex-1">
      <label className="flex h-12 items-center gap-2 rounded-full bg-chip px-4 focus-within:ring-4 focus-within:ring-accent/25">
        <svg aria-hidden viewBox="0 0 24 24" className="h-4 w-4 shrink-0 text-muted">
          <path fill="currentColor" d="M10 2a8 8 0 0 1 6.32 12.9l5.39 5.4-1.42 1.4-5.39-5.38A8 8 0 1 1 10 2Zm0 2a6 6 0 1 0 0 12 6 6 0 0 0 0-12Z" />
        </svg>
        <span className="sr-only">Search stories</span>
        <input
          key={q}
          name="q"
          type="search"
          defaultValue={q}
          maxLength={80}
          placeholder="Search founder stories"
          className="w-full min-w-0 bg-transparent text-[15px] outline-none placeholder:text-muted"
        />
      </label>
    </form>
  );
}
