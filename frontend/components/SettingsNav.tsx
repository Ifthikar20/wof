"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/settings", label: "Profile" },
  { href: "/settings/security", label: "Security" },
];

export function SettingsNav() {
  const path = usePathname();
  return (
    <nav className="mt-4 flex gap-1 overflow-x-auto md:flex-col">
      {ITEMS.map((i) => (
        <Link key={i.href} href={i.href}
              className={`whitespace-nowrap rounded-xl px-3 py-2 text-sm font-semibold ${path === i.href ? "bg-ink text-bg" : "hover:bg-chip"}`}>
          {i.label}
        </Link>
      ))}
    </nav>
  );
}
