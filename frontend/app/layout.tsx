import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import "./globals.css";
import { HeaderActions } from "@/components/HeaderActions";

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
        <header className="sticky top-0 z-20 border-b border-line bg-bg/90 backdrop-blur">
          <div className="mx-auto flex max-w-[1600px] items-center gap-4 px-4 py-3">
            <Link href="/" className="flex items-center gap-2 font-serif text-xl font-bold tracking-tight">
              <span aria-hidden className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-accent-ink text-sm font-sans">W</span>
              <span className="hidden sm:inline">Wall of Founders</span>
            </Link>
            <nav className="flex items-center gap-1 text-sm">
              <Link href="/" className="rounded-full px-3 py-1.5 hover:bg-surface">Wall</Link>
              <Link href="/digest" className="rounded-full px-3 py-1.5 hover:bg-surface">Digest</Link>
            </nav>
            <div className="ml-auto"><HeaderActions /></div>
          </div>
        </header>
        <main className="mx-auto max-w-[1600px] px-4 py-6">{children}</main>
        <footer className="mx-auto max-w-[1600px] px-4 py-10 text-sm text-muted">
          Every story is written by a founder we verified by hand. Every edit is versioned and publicly hashed.
        </footer>
      </body>
    </html>
  );
}
