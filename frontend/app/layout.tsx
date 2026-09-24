import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { Suspense } from "react";
import "./globals.css";
import { HeaderActions } from "@/components/HeaderActions";
import { HeaderNav } from "@/components/HeaderNav";
import { SearchBar } from "@/components/SearchBar";

export const metadata: Metadata = {
  title: { default: "Wall of Founders", template: "%s · Wall of Founders" },
  description: "True stories from verified founders. Read them on the wall, or get the best ones in your inbox every week.",
  robots: { index: true, follow: true },
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Reading the per-request nonce opts every page into dynamic rendering, which the
  // nonce-based CSP requires (Next.js stamps the nonce onto its own <script> tags).
  await headers();
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="sticky top-0 z-20 bg-bg">
          <div className="mx-auto flex max-w-[1880px] items-center gap-2 px-4 py-2">
            <Link href="/" aria-label="Wall of Founders home" className="grid h-12 w-12 shrink-0 place-items-center rounded-full hover:bg-chip">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-accent text-sm font-bold text-accent-ink">W</span>
            </Link>
            <HeaderNav />
            <Suspense fallback={<div className="h-12 flex-1 rounded-full bg-chip" />}>
              <SearchBar />
            </Suspense>
            <HeaderActions />
          </div>
        </header>
        <main className="mx-auto max-w-[1880px] px-4 pb-6 pt-2">{children}</main>
        <footer className="mx-auto max-w-[1880px] px-4 py-10 text-center text-sm text-muted">
          Every story is written by a founder we verified by hand. Every edit is versioned and publicly hashed.
        </footer>
      </body>
    </html>
  );
}
