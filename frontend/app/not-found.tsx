import Link from "next/link";
import { LogoMark } from "@/components/Logo";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center py-28 text-center">
      <LogoMark className="h-14 w-14 opacity-80" />
      <p className="mt-8 text-xs font-semibold uppercase tracking-[.18em] text-muted">404</p>
      <h1 className="mt-2 font-serif text-6xl leading-none">Nothing on this part of the wall.</h1>
      <p className="mt-4 max-w-md text-muted">The story may have been removed by its author, or the link is mistyped.</p>
      <Link href="/" className="btn btn-primary mt-8 h-12 px-6">Back to the wall</Link>
    </div>
  );
}
