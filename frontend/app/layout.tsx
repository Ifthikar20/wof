import type { Metadata } from "next";
import { headers } from "next/headers";
import Link from "next/link";
import { Suspense } from "react";
import "./globals.css";
import { AuthPrompt } from "@/components/AuthPrompt";
import { HeaderActions } from "@/components/HeaderActions";
import { HeaderNav } from "@/components/HeaderNav";
import { Logo } from "@/components/Logo";
import { SearchBar } from "@/components/SearchBar";
import { SessionProvider } from "@/components/SessionProvider";

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
        <SessionProvider>
        <div className="ambient" aria-hidden><span /><span /><span /></div>
        <header className="glass sticky top-0 z-20 border-b border-line/60">
          <div className="mx-auto flex max-w-[1880px] items-center gap-3 px-4 py-2.5 sm:px-6">
            <Link href="/" aria-label="Wall of Founders home" className="shrink-0 rounded-full pr-2">
              <span className="hidden lg:inline"><Logo /></span>
              <span className="lg:hidden"><Logo withWordmark={false} /></span>
            </Link>
            <HeaderNav />
            <Suspense fallback={<div className="h-11 flex-1 rounded-full bg-chip" />}>
              <SearchBar />
            </Suspense>
            <HeaderActions />
          </div>
        </header>
        <main className="mx-auto max-w-[1880px] px-4 pb-6 pt-4 sm:px-6">{children}</main>
        <footer className="mx-auto flex max-w-[1880px] flex-col items-center gap-3 px-4 py-14 text-center text-sm text-muted">
          <Logo withWordmark={false} />
          Every story is written by a founder we verified by hand. Every edit is versioned and publicly hashed.
        </footer>
        <AuthPrompt />
        </SessionProvider>
      </body>
    </html>
  );
}
