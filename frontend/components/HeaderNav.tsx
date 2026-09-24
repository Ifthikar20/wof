"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/digest", label: "Digest" },
];

export function HeaderNav() {
  const path = usePathname();
  return (
    <nav className="hidden items-center gap-1 sm:flex">
      {LINKS.map(({ href, label }) => {
        const active = href === "/" ? path === "/" : path.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={`rounded-full px-4 py-3 text-[15px] font-semibold ${active ? "bg-ink text-bg" : "hover:bg-chip"}`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
